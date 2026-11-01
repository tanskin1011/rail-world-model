"""Link a successful native run as local configuration; never copies model weights."""
from pathlib import Path
import argparse,json,shutil,sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference-run',type=Path,required=True)
    parser.add_argument('--bank',type=Path,required=True)
    parser.add_argument('--inventory-sources',type=Path,required=True)
    args=parser.parse_args()
    project=Path(__file__).resolve().parents[1]
    source=args.reference_run.resolve()
    plan=json.loads((source/'RUN_PLAN.json').read_text())
    out=project/'internal';out.mkdir(exist_ok=True)
    if (out/'runtime.json').exists():raise SystemExit('Preserve existing runtime.json; edit a separately named profile instead')
    for name in ['MODEL_CONFIG.json','EXPECTED_B1097_TYPED.json']:
        target=out/('inference_'+name)
        if target.exists():raise SystemExit('Preserve '+str(target))
        shutil.copy2(source/name,target)
    framework=Path(plan['repo'])
    cfg=json.loads((out/'inference_MODEL_CONFIG.json').read_text())['model']['config']
    data=dict(python=plan['python'],framework=str(framework),checkpoint=plan['checkpoint'],
        model_config=str(out/'inference_MODEL_CONFIG.json'),expected_weights=str(out/'inference_EXPECTED_B1097_TYPED.json'),
        ffmpeg=plan['ffmpeg'],guard_sources=str(source),inventory_sources=str(args.inventory_sources.resolve()),
        bank=str(args.bank.resolve()),reference_run=str(source),
        environment=dict(BASE_CHECKPOINT_PATH=str(framework/'examples/checkpoints/Cosmos3-Nano'),
            WAN_VAE_PATH=cfg['tokenizer']['vae_path'],IMAGEIO_FFMPEG_EXE=plan['ffmpeg'],
            HF_HOME=str(Path.home()/'.cache/huggingface'),HF_HUB_CACHE=str(Path.home()/'.cache/huggingface/hub'),
            HF_DATASETS_OFFLINE='1',WANDB_MODE='disabled',AWS_EC2_METADATA_DISABLED='true'))
    (out/'runtime.json').write_text(json.dumps(data,indent=2))
    # Real examples remain local, ignored by Git; these are references, not copied media.
    example=json.loads((source/'INPUT.json').read_text())
    (out/'example_prompt.txt').write_text(example['prompt']+'\n')
    (out/'example_input.json').write_text(json.dumps(example,indent=2))
    print(out/'runtime.json')


if __name__=='__main__':main()
