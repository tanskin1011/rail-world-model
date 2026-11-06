"""Native Omni FD adapter, using the previously validated model API."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check-stdin',action='store_true')
    parser.add_argument('request',type=Path,nargs='?')
    args=parser.parse_args()
    spec=json.load(sys.stdin) if args.check_stdin else json.loads(args.request.read_text())
    runtime=spec['runtime'];sys.path.insert(0,runtime['framework'])
    import torch
    from PIL import Image
    from omegaconf import OmegaConf
    from cosmos_framework.inference.args import OmniSampleOverrides
    cfg=json.loads(Path(runtime['model_config']).read_text())['model']
    output=Path(spec['output'])/'video'
    with Image.open(spec['sample']['vision_path']) as image:
        image.load()
        if image.size!=(832,480) or image.mode!='RGB':
            raise ValueError('Expected RGB PNG 832x480; no implicit conversion')
    sample=OmniSampleOverrides(**spec['sample'],output_dir=output).build_sample(model_config=OmegaConf.create(cfg['config']))
    effective=json.loads(sample.model_dump_json())
    if sample.model_mode.value!='forward_dynamics' or sample.domain_name!='camera_pose' or sample.condition_frame_indexes_vision!=[0]:
        raise ValueError('Not first-frame camera-conditioned FD')
    if sample.num_frames!=189 or sample.action_chunk_size!=188 or sample.fps!=24:
        raise ValueError('Unexpected sample geometry')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(cfg['config']['vlm_config']['tokenizer']['pretrained_model_name'],local_files_only=True)
    tokens=tokenizer(spec['sample']['prompt'],truncation=False)['input_ids']
    if len(tokens)>1024:
        raise ValueError('This fixed CLI profile limits scene prompts to 1024 tokens')
    check=dict(status='PASS_CPU_CHECK',model_loaded=False,cuda_initialized=torch.cuda.is_initialized(),
               action_shape=[188,9],image_shape=[480,832,3],prompt_tokens=len(tokens),
               prompt_truncated=False,effective_args=effective)
    if args.check_stdin:
        if check['cuda_initialized']:
            raise RuntimeError('CPU check unexpectedly initialized CUDA')
        print(json.dumps(check));return
    if os.environ.get('RAIL_CLI_WORKER_AUTHORIZED')!=str(os.getppid()):
        raise RuntimeError('Worker must be started by its resource supervisor')
    def write(name,data):
        path=Path(spec['output'])/name
        temp=path.with_suffix(path.suffix+'.writing')
        temp.write_text(json.dumps(data,indent=2));temp.replace(path)
    def phase(activity):
        write('phase.json',dict(phase='initialize' if activity=='load_model' else 'verify',activity=activity))
    def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    for key,hashkey in [('model_config','model_config_sha256'),('expected_weights','expected_weights_sha256')]:
        if sha(runtime[key])!=spec[hashkey]:raise RuntimeError('Runtime changed after CPU check: '+key)
    for key,hashkey in [('vision_path','image_sha256'),('action_path','action_sha256')]:
        if sha(spec['sample'][key])!=spec[hashkey]:raise RuntimeError('Input changed after CPU check: '+key)
    import cosmos_framework.utils.checkpoint_db as db
    def reject(*a,**kw):raise RuntimeError('Downloads disabled; local assets only')
    db._hf_download=reject;db.CheckpointDirHf._download=reject;db.CheckpointFileHf._download=reject
    from cosmos_framework.inference.common.init import init_script
    init_script()
    from cosmos_framework.inference.model import Cosmos3OmniConfig,Cosmos3OmniModel
    from cosmos_framework.configs.base.defaults.parallelism import ParallelismConfig
    from cosmos_framework.configs.base.defaults.compile import CompileConfig
    from torch.distributed.checkpoint.state_dict import get_model_state_dict
    from cosmos_framework.inference.inference import get_sample_data
    from cosmos_framework.tools.visualize.video import save_img_or_video
    torch.set_num_threads(2)
    torch.set_grad_enabled(False)
    phase('load_model')
    bundle=Cosmos3OmniModel.from_pretrained_dcp(Path(runtime['checkpoint'])/'model',
        config=Cosmos3OmniConfig(model=cfg),
        parallelism_config=ParallelismConfig(data_parallel_shard_degree=1,data_parallel_replicate_degree=1,context_parallel_shard_degree=1,cfg_parallel_shard_degree=1),
        compile_config=CompileConfig(enabled=False,use_cuda_graphs=False))
    model=bundle.model;model.eval();model.requires_grad_(False)
    expected=json.loads(Path(runtime['expected_weights']).read_text())
    state=get_model_state_dict(model)
    if set(state)!=set(expected):raise RuntimeError('Loaded weight keys do not match Rail World Model')
    for key,value in state.items():
        value=value.to_local() if hasattr(value,'to_local') else value
        value=value.detach().cpu().contiguous()
        h=hashlib.sha256();h.update(str(value.dtype).encode());h.update(str(tuple(value.shape)).encode())
        h.update(memoryview(value.reshape(-1).view(torch.uint8).numpy()).cast('B'))
        if h.hexdigest()!=expected[key]:raise RuntimeError('Weight mismatch: '+key)
    write('WEIGHTS_VERIFIED.json',dict(status='PASS',tensors=len(state),checkpoint=runtime['checkpoint'],training=False))
    del state,value
    output.mkdir(exist_ok=False)
    sample=OmniSampleOverrides(**spec['sample'],output_dir=output).build_sample(model_config=model.config)
    if json.loads(sample.model_dump_json())!=effective:raise RuntimeError('Effective args changed after model load')
    (output/'sample_args.json').write_text(sample.model_dump_json(indent=2))
    data=get_sample_data(sample,model)
    plan=data['sequence_plan'][0]
    if plan.condition_frame_indexes_vision!=[0] or plan.condition_frame_indexes_action!=list(range(188)):
        raise RuntimeError('Incorrect native conditioning mask')
    if int(data['domain_id'][0])!=2 or tuple(data['action'][0][0].shape)!=(188,64):
        raise RuntimeError('Incorrect camera action domain or tensor')
    write('CONDITIONING_VERIFIED.json',dict(vision=[0],actions=list(range(188)),domain_id=2,padded_action_shape=[188,64]))
    began=time.monotonic();phase('generate')
    result=model.generate_samples_from_batch(data,sampler=None,guidance=sample.guidance,
        guidance_interval=sample.guidance_interval,seed=[sample.seed],num_steps=sample.num_steps,
        shift=sample.shift,sigma_max=sample.sigma_max,normalize_cfg=sample.normalize_cfg,
        n_sample=1,has_negative_prompt=False,upsample_task=None)
    phase('decode_gpu')
    video=model.decode(result['vision'][0])
    if tuple(video.shape)!=(1,3,189,480,832) or not bool(torch.isfinite(video).all()):raise RuntimeError('Invalid decoded video')
    save_img_or_video(((video+1)/2).clamp(0,1)[0],str(output/'vision'),fps=24)
    phase('full_decode_cpu')
    import imageio_ffmpeg
    reader=imageio_ffmpeg.read_frames(str(output/'vision.mp4'),pix_fmt='rgb24')
    metadata=next(reader);count=sum(1 for _ in reader)
    if count!=189 or metadata['fps']!=24 or tuple(metadata['size'])!=(832,480):raise RuntimeError('MP4 geometry mismatch')
    decoded=subprocess.run([runtime['ffmpeg'],'-v','error','-nostdin','-i',str(output/'vision.mp4'),'-f','null','-'],capture_output=True,text=True)
    if decoded.returncode or decoded.stderr.strip():raise RuntimeError(decoded.stderr)
    write('RESULT.json',dict(status='COMPLETE',video=str(output/'vision.mp4'),frames=count,fps=24,width=832,height=480,
         elapsed_s=time.monotonic()-began,video_sha256=sha(output/'vision.mp4'),semantic_review_pending=True,training=False))
    phase('complete')


if __name__=='__main__':main()
