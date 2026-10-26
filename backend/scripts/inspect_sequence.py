"""Runnable evidence-risk check, using exactly the worker's analysis functions."""
import argparse
import html
import json
import subprocess
import uuid
from pathlib import Path

from backend.app.analysis.pipeline import register_clip, prepare_clip, analyse, save_json, extract_selected
from backend.app.config import DATA


def write_review(path, report):
    """Readable local evidence companion, never a detection mockup."""
    cards = []
    for result in report['updated']['results']:
        frames = []
        for key, label in [('reference_evidence', 'A / Reference'), ('candidate_evidence', 'B / Comparison')]:
            evidence = result[key]
            source = (DATA / 'evidence' / evidence['id'] / 'frame.jpg').as_uri()
            polygon = evidence.get('effective_polygon')
            points = ' '.join(f'{x*100},{y*100}' for x, y in polygon) if polygon else ''
            overlay = f'<polygon points="{points}" fill="none" stroke="#ba1a1a" stroke-width="0.3"/>' if points else ''
            frames.append(f'<figure><figcaption>{label} · {html.escape(evidence["clip_id"])} · '
                          f'{evidence["time_ms"]:.2f} ms · frame {evidence["ordinal"]}</figcaption>'
                          f'<div class="image"><img src="{source}"><svg viewBox="0 0 100 100" '
                          f'preserveAspectRatio="none">{overlay}</svg></div></figure>')
        score = 'Not assessable' if result['score'] is None else f'Appearance difference: {result["score"]:.2f} / 100'
        cards.append(f'<article><h2>{html.escape(result["description"])}</h2><p>{score} · '
                     f'Reference {html.escape(result["reference_id"][:8])}</p><div class="pair">'
                     + ''.join(frames) + '</div><p>' + html.escape(', '.join(result['reasons'])) + '</p></article>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Continuity Detective — evidence inspection</title>
<style>body{font:14px system-ui;background:#fbf9f6;color:#191918;margin:32px}h1{font-size:24px}h2{font-size:16px}
article{border:1px solid #e5e3df;background:white;padding:20px;margin:20px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}
figure{margin:0}figcaption{font:12px monospace;margin-bottom:10px}.image{position:relative}.image img{width:100%;display:block}
.image svg{position:absolute;inset:0;width:100%;height:100%}p{color:#6b665f}@media(max-width:700px){.pair{grid-template-columns:1fr}}
</style><h1>Continuity Detective / Evidence inspection</h1><p>Experimental colour measurements. Provisional thresholds. Not confidence, garment identity or story-intent inference.</p>'''
    path.write_text(page + ''.join(cards) + '</html>', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('clips', nargs='+', type=Path)
    parser.add_argument('--reference', required=True, help='Zero-based clip index:time in milliseconds')
    parser.add_argument('--new-reference', action='append', default=[])
    parser.add_argument('--crop', nargs=4, type=float, metavar=('X', 'Y', 'W', 'H'),
                        help='Optional normalized crop override for the initial reference')
    parser.add_argument('--output', type=Path, default=Path('data/inspection/report.json'))
    args = parser.parse_args()
    if not 1 <= len(args.clips) <= 3:
        parser.error('Inspect one to three clips')
    if any(not path.is_file() for path in args.clips):
        parser.error('Every clip must be an existing local file')
    if sum(path.stat().st_size for path in args.clips) > 250 * 1024 * 1024:
        parser.error('Sequence exceeds the current 250 MiB limit')
    if args.crop:
        x, y, w, h = args.crop
        if min(x, y) < 0 or min(w, h) <= 0 or x + w > 1 or y + h > 1:
            parser.error('Crop must be within normalized image bounds')
    selections = [args.reference, *args.new_reference]
    parsed = []
    for selection in selections:
        try:
            index, time = selection.split(':')
            index, time = int(index), float(time)
            if not 0 <= index < len(args.clips) or time < 0:
                raise ValueError('out of range')
            parsed.append((index, time))
        except (ValueError, IndexError):
            parser.error(f'Invalid reference {selection!r}: use clip index:milliseconds')
    # Actual boundaries are checked again after exact-frame resolution below.
    if any(new <= old for old, new in zip(parsed[1:], parsed[2:])):
        parser.error('New reference boundaries must be in increasing sequence order')
    clips = [prepare_clip(register_clip(path, f'clip-{index}'),
                          progress=lambda n, total, phase: print(f'{phase}: {n}/{total}', flush=True))
             for index, path in enumerate(args.clips)]
    references = []
    for i, selection in enumerate([args.reference, *args.new_reference]):
        try:
            index, time = selection.split(':')
            index, time = int(index), float(time)
            if index < 0 or index >= len(clips):
                raise ValueError('clip index out of range')
            clip = clips[index]
            if not 0 <= time <= clip['metadata']['duration_ms']:
                raise ValueError('timestamp out of range')
        except (ValueError, IndexError):
            parser.error(f'Invalid reference {selection!r}: use clip index:milliseconds within the source')
        frame = extract_selected(clip, time)
        references.append({'id': str(uuid.uuid4()), 'confirmed': True, 'evidence_id': frame['id'],
                           'crop': args.crop if i == 0 and args.crop else frame['crop'],
                           'start_clip_id': clips[0]['id'] if i == 0 else clip['id'],
                           'start_ms': 0 if i == 0 else frame['time_ms']})
    order = [clip['id'] for clip in clips]
    starts = [(order.index(ref['start_clip_id']), ref['start_ms']) for ref in references]
    if any(new <= old for old, new in zip(starts, starts[1:])):
        parser.error('Resolved new reference boundaries must follow the preceding reference')
    baseline = analyse(clips, references[:1])
    updated = analyse(clips, references)
    report = {'baseline': baseline, 'updated': updated,
              'evidence_root': str(Path('data/evidence').resolve()),
              'warning': 'Experimental measured colour differences, not garment identity or intent inference.'}
    save_json(args.output, report)
    review_path = args.output.with_suffix('.html')
    write_review(review_path, report)
    print(json.dumps({'report': str(args.output.resolve()),
                      'review': str(review_path.resolve()),
                      'outcomes': {status: sum(r['status'] == status for r in updated['results'])
                                   for status in ['difference', 'no_difference_flagged', 'not_assessable']}}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        raise SystemExit(f'Inspection failed: {error}') from error
