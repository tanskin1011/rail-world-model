"""CPU-only publication copies; original media and temporal order are preserved."""
from pathlib import Path
import argparse,hashlib,json,subprocess


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe(path):
    result=subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
        '-show_entries','stream=codec_name,pix_fmt,width,height,avg_frame_rate,nb_read_frames','-of','json',str(path)],text=True)
    return json.loads(result)['streams'][0]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sources',type=Path,required=True)
    parser.add_argument('--dest',type=Path,required=True)
    parser.add_argument('--private-report',type=Path,required=True)
    args=parser.parse_args()
    from PIL import Image,ImageDraw,ImageFont
    args.dest.mkdir(parents=True,exist_ok=False)
    spec=json.loads(args.sources.read_text());public=[];private=[]
    fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font=ImageFont.truetype(fontpath,22)
    for item in spec['comparisons']:
        paths=[Path(p) for p in item['videos']]
        for p in paths:
            meta=probe(p)
            assert meta['width']==832 and meta['height']==480 and meta['avg_frame_rate']=='24/1' and int(meta['nb_read_frames'])==189,(p,meta)
        output=args.dest/(item['id']+'.mp4')
        filters=[]
        for i,label in enumerate(item['labels']):
            assert all(c.isalnum() or c in ' |+-' for c in label)
            filters.append(f"[{i}:v]setpts=PTS-STARTPTS,pad=832:528:0:48:color=0x18283b,drawtext=fontfile={fontpath}:text='{label}':fontcolor=white:fontsize=23:x=16:y=12[v{i}]")
        filters.append('[v0][v1]hstack=inputs=2[out]')
        command=['ffmpeg','-v','error','-nostdin','-n','-i',str(paths[0]),'-i',str(paths[1]),
            '-filter_complex',';'.join(filters),'-map','[out]','-an','-c:v','libx264','-preset','medium','-crf','20',
            '-pix_fmt','yuv420p','-movflags','+faststart','-map_metadata','-1',str(output)]
        subprocess.run(command,check=True)
        info=probe(output)
        assert info['width']==1664 and info['height']==528 and info['avg_frame_rate']=='24/1' and int(info['nb_read_frames'])==189 and info['pix_fmt']=='yuv420p',info
        subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(output),'-f','null','-'],check=True)
        # Representative frames are extracted from originals, not the publication encode.
        canvas=Image.new('RGB',(1664,3*528),'#18283b');draw=ImageDraw.Draw(canvas)
        for row,index in enumerate([0,96,188]):
            for col,(p,label) in enumerate(zip(paths,item['labels'])):
                payload=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-vf',f'select=eq(n\\,{index})','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
                assert len(payload)==832*480*3
                canvas.paste(Image.frombytes('RGB',(832,480),payload),(col*832,row*528+48))
                draw.text((col*832+12,row*528+12),f'{label} | t={index/24:.2f}s',font=font,fill='white')
        sheet=args.dest/(item['id']+'.jpg');canvas.save(sheet,quality=91)
        record=dict(id=item['id'],kind=item['kind'],video=output.name,preview=sheet.name,labels=item['labels'],
            request=item['request'],observation=item['observation'],limit=item['limit'],seed=401,
            frames=189,fps=24,native_tile_size=[832,480],edited_size=[1664,528],
            preview_frame_indexes=[0,96,188],source_video_sha256=[sha(p) for p in paths],
            output_sha256=sha(output),preview_sha256=sha(sheet),full_decode_pass=True,
            video_codec='h264',pixel_format='yuv420p',original_frame_order_and_speed_preserved=True,
            new_inference=False)
        public.append(record);private.append(dict(id=item['id'],sources=[str(p) for p in paths],command=command,metadata=info))
    for item in spec['images']:
        p=Path(item['path']);output=args.dest/(item['id']+'.png')
        with Image.open(p) as image:
            image.convert('RGB').save(output)
        public.append(dict(id=item['id'],kind='synthetic_training_frame',image=output.name,
            caption=item['caption'],source_sha256=sha(p),output_sha256=sha(output),new_generation=False))
        private.append(dict(id=item['id'],source=str(p)))
    (args.dest/'manifest.json').write_text(json.dumps(public,indent=2,ensure_ascii=False))
    with args.private_report.open('x') as stream:json.dump(private,stream,indent=2)
    print(json.dumps(dict(publication_copies=len(public),new_inference=False,destination=str(args.dest)),indent=2))


if __name__=='__main__':main()
