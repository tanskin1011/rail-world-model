"""Check the staged source tree in a fresh venv without private assets or pip."""
from pathlib import Path
import argparse,io,json,os,re,subprocess,sys,tarfile,tempfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    tree=subprocess.check_output(['git','write-tree'],cwd=root,text=True).strip()
    archive=subprocess.check_output(['git','archive',tree],cwd=root)
    with tempfile.TemporaryDirectory(prefix='rail-wm-clean-cpu-') as directory:
        temp=Path(directory);checkout=temp/'source';checkout.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(checkout,filter='data')
        for forbidden in ['internal','outputs','datasets','checkpoints']:
            if (checkout/forbidden).exists():raise RuntimeError('Private directory in exported tree: '+forbidden)
        subprocess.run([sys.executable,'-m','venv','--without-pip',str(temp/'venv')],check=True)
        python=temp/'venv/bin/python'
        env=dict(os.environ,PYTHONPATH=str(checkout/'src'),PYTHONNOUSERSITE='1',CUDA_VISIBLE_DEVICES='')
        tests=subprocess.run([str(python),'-m','unittest','discover','-s','tests','-v'],cwd=checkout,env=env,capture_output=True,text=True)
        if tests.returncode:raise RuntimeError(tests.stdout+tests.stderr)
        profiles=[]
        for profile in ['stop','const5','const10','accel','decel']:
            target=temp/(profile+'.json')
            for operation in [['make-action','--profile',profile,'--output',str(target)],['validate-action',str(target),'--transitions','188']]:
                run=subprocess.run([str(python),'-m','rail_world_model',*operation],cwd=checkout,env=env,capture_output=True,text=True)
                if run.returncode:raise RuntimeError(run.stdout+run.stderr)
            profiles.append(profile)
        version=subprocess.check_output([str(python),'--version'],text=True).strip()
        report=dict(status='PASS_CLEAN_CPU',source_tree=tree,python=version,
            unit_tests=int(re.search(r'Ran (\d+) tests',tests.stderr).group(1)),
            profiles_generated_and_validated=profiles,private_assets_present=False,
            external_python_packages_installed=False,gpu_model_loaded=False,
            different_physical_machine_tested=False,
            scope='Fresh exported source and isolated stdlib venv on the same host; not cross-device GPU verification')
        args.report.parent.mkdir(parents=True,exist_ok=True)
        with args.report.open('x') as stream:json.dump(report,stream,indent=2)
        print(json.dumps(report,indent=2))


if __name__=='__main__':main()
