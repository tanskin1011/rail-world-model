"""Check public working-tree candidates or the explicit staged tree in isolation."""
from pathlib import Path
import argparse,hashlib,io,json,os,re,shutil,subprocess,sys,tarfile,tempfile
from audit_release import audit,candidate_paths


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--staged',action='store_true',help='Check Git index instead of current public working-tree files')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    if args.report.exists():raise FileExistsError(args.report)
    tree=None
    with tempfile.TemporaryDirectory(prefix='rail-wm-clean-cpu-') as directory:
        temp=Path(directory);checkout=temp/'source';checkout.mkdir()
        if args.staged:
            tree=subprocess.check_output(['git','write-tree'],cwd=root,text=True).strip()
            archive=subprocess.check_output(['git','archive',tree],cwd=root)
            with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
                bundle.extractall(checkout,filter='data')
            names=[p.relative_to(checkout).as_posix() for p in checkout.rglob('*') if p.is_file() or p.is_symlink()]
        else:
            names=candidate_paths(root)
            issues=audit(root,names)
            if issues:raise RuntimeError(str(issues))
            for name in names:
                target=checkout/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(root/name,target)
        issues=audit(checkout,names)
        if issues:raise RuntimeError(str(issues))
        manifest={name:hashlib.sha256((checkout/name).read_bytes()).hexdigest() for name in sorted(names)}
        for forbidden in ['internal','local','nano','outputs','datasets','checkpoints']:
            if (checkout/forbidden).exists():raise RuntimeError('Private directory in exported tree: '+forbidden)
        subprocess.run([sys.executable,'-m','venv','--without-pip',str(temp/'venv')],check=True)
        python=temp/'venv/bin/python'
        env=dict(os.environ,PYTHONPATH=str(checkout/'src'),PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='')
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
        report=dict(status='PASS_CLEAN_CPU',source_tree=tree,source_mode='staged' if args.staged else 'working-tree-candidates',files_sha256=manifest,python=version,
            unit_tests=int(re.search(r'Ran (\d+) tests',tests.stderr).group(1)),
            profiles_generated_and_validated=profiles,private_assets_present=False,
            external_python_packages_installed=False,gpu_model_loaded=False,
            different_physical_machine_tested=False,
            scope='Fresh exported source and isolated stdlib venv on the same host; not cross-device GPU verification')
        args.report.parent.mkdir(parents=True,exist_ok=True)
        with args.report.open('x') as stream:json.dump(report,stream,indent=2)
        print(json.dumps(report,indent=2))


if __name__=='__main__':main()
