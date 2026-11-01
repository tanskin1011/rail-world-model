"""Resource-supervised native worker, detached by the TAO virtualenv runner."""
from pathlib import Path
from dataclasses import asdict,replace
import json,os,signal,subprocess,sys,time


def main():
    spec_path=Path(sys.argv[1]);spec=json.loads(spec_path.read_text());runtime=spec['runtime']
    root=Path(spec['output'])
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from rail_world_model.infer_cli import worker_environment
    sys.path[:0]=[runtime['guard_sources'],runtime['inventory_sources']]
    from telemetry import Heartbeat,Reader,parse_proc_start_ticks
    from monitor_candidate import Policy,OfflineMonitor,start_gate
    from gpu_inventory import gpu_processes
    policy=replace(Policy(),start_ram_gib=0,ram_floor_gib=48,disk_floor_gib=60,swap_growth_cap_gib=1,save_cap_s=600,diagnostic_wall_cap_s=93600)
    def write(name,data):(root/name).write_text(json.dumps(data,indent=2))
    def ticks(pid):return parse_proc_start_ticks(Path('/proc',str(pid),'stat').read_text())
    def belongs(pid,owner):
        seen=set()
        while pid>1 and pid not in seen:
            if pid==owner:return True
            seen.add(pid)
            try:pid=int(Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[1])
            except (OSError,ValueError):return False
        return False
    if gpu_processes():raise RuntimeError('Other GPU compute job detected; nothing stopped')
    write('phase.json',dict(phase='initialize',activity='resource_gate'))
    write('RESOURCE_POLICY.json',asdict(policy))
    heartbeat=Heartbeat();reader=Reader(root,heartbeat);child=None
    try:
        for _ in range(60):
            sample,detail=reader.read(time.monotonic(),os.getpid(),ticks(os.getpid()),0);time.sleep(1)
        gate=start_gate(sample,policy)
        if gate.status!='OK':raise RuntimeError(str(asdict(gate)))
        if gpu_processes():raise RuntimeError('GPU became occupied during resource check')
        baseline=sample.swap_used_gib
        env=worker_environment(runtime)
        env.update(CUDA_VISIBLE_DEVICES='0',RAIL_CLI_WORKER_AUTHORIZED=str(os.getpid()))
        command=[runtime['python'],str(Path(__file__).with_name('native_worker.py')),str(spec_path)]
        write('WORKER_COMMAND.json',command)
        with (root/'worker.stdout.log').open('x') as out,(root/'worker.stderr.log').open('x') as err:
            # Same process group as the platform wrapper: platform cancel owns the entire group.
            child=subprocess.Popen(command,env=env,cwd=runtime['framework'],stdout=out,stderr=err)
        identity=ticks(child.pid);monitor=OfflineMonitor(time.monotonic(),policy)
        while child.poll() is None:
            sample,detail=reader.read(time.monotonic(),child.pid,identity,baseline)
            verdict=monitor.evaluate(sample)
            foreign=[x for x in gpu_processes() if not belongs(x['pid'],child.pid)]
            with (root/'resources.jsonl').open('a') as stream:stream.write(json.dumps(dict(sample=asdict(sample),verdict=asdict(verdict)))+'\n')
            if foreign or verdict.status in ['WOULD_STOP_JOB','MONITOR_IDENTITY_LOST']:
                if ticks(child.pid)==identity:child.terminate()
                raise RuntimeError('Resource guard stopped owned inference: '+str(foreign or asdict(verdict)))
            time.sleep(1)
        code=child.wait()
        if code:raise RuntimeError(f'Worker exited {code}; see worker.stderr.log')
        result=json.loads((root/'RESULT.json').read_text())
        if result['status']!='COMPLETE':raise RuntimeError('Missing verified completion')
    except BaseException as error:
        write('ERROR.json',dict(error=repr(error),training=False))
        if child is not None and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=20)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        raise
    finally:heartbeat.close()


if __name__=='__main__':main()
