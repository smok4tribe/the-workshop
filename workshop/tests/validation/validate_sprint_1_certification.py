#!/usr/bin/env python3
"""Validate the Sprint 1 certification candidate without self-certifying it."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PROJECT_ID=os.environ.get('WORKSHOP_PROJECT_ID','the-myr-singularity')
PROJECT=ROOT/'workshop'/'projects'/PROJECT_ID

def load(path): return json.loads(path.read_text(encoding='utf-8'))
def render_module():
    import importlib.util
    path=ROOT/'workshop'/'scripts'/'render_sprint_1_closure.py'
    spec=importlib.util.spec_from_file_location('closure_renderer',path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def emit(checks):
    failed=0
    for name,errors in checks:
        print(f"[{'PASS' if not errors else 'FAIL'}] {name}")
        for error in errors: print(f'       - {error}')
        failed+=bool(errors)
    print(); print(f"{'FAIL: '+str(failed)+' of '+str(len(checks))+' certification checks failed.' if failed else 'PASS: all '+str(len(checks))+' Sprint certification checks passed.'}")
    return 1 if failed else 0
def main():
    checks=[]; cert_path=PROJECT/'reports'/'sprint_1_certification.json'; errors=[]
    try: cert=load(cert_path)
    except (OSError,json.JSONDecodeError) as exc: return emit([('certification artifact parses',[str(exc)])])
    checks.append(('certification identity',[] if cert.get('certification_id') and cert.get('project_id')==PROJECT_ID and cert.get('sprint_id')=='Sprint 1' and cert.get('certification_scope')=='sprint_1_local_prototype' else ['certification identity or scope is invalid']))
    review=cert.get('independent_review',{}); status=cert.get('certification_status'); errors=[]
    if status not in {'pending_independent_review','certified','certified_with_non_blocking_followups','not_certified'}: errors.append('unsupported certification status')
    if status=='pending_independent_review' and any(review.get(k) is not None for k in ('reviewer','verdict','reviewed_commit','reviewed_at','review_source')): errors.append('pending independent review must not contain completed review fields')
    if status=='pending_independent_review' and review.get('status')!='pending': errors.append('pending certification requires pending independent review')
    if status in {'certified','certified_with_non_blocking_followups'} and (review.get('status')!='completed' or review.get('verdict')!='APPROVE' or not all(review.get(k) for k in ('reviewer','reviewer_role','reviewed_commit','reviewed_at','review_source')) or review.get('blocking_findings')): errors.append('completed certification requires approving independent review')
    checks.append(('independent review semantics',errors))
    errors=[]
    for key,value in cert.get('source_references',{}).items():
        for ref in value if isinstance(value,list) else [value]:
            if not isinstance(ref,dict) or not (ROOT/ref.get('path','')).is_file(): errors.append(f"source {key!r} does not resolve")
    checks.append(('structured sources resolve',errors))
    errors=[]
    if [x.get('title') for x in cert.get('product_loop',[])] != ['Project','Brief','Deck Import','Baseline DeckVersion','Card Facts','Functional Knowledge','Baseline Analysis','Structural Weakness','Recommendation','Product Owner Review','Decision','Deck-change Design','Product Owner Approval','Resulting DeckVersion','Report'] or any(x.get('status')!='complete' for x in cert.get('product_loop',[])): errors.append('product loop is incomplete or out of order')
    if any(x.get('status') not in {'pass','pending_external_review'} for x in cert.get('sprint_exit_criteria',[])): errors.append('exit criteria contain non-passing status')
    checks.append(('product loop and exit criteria',errors))
    errors=[]; backlog=load(PROJECT/'notes'/'backlog.json'); ids={x.get('backlog_id') for x in backlog.get('items',[])}
    if not set(cert.get('deferred_backlog_ids',[])) <= ids: errors.append('required deferred backlog items are not captured')
    if any('Placeholder.' in (ROOT/'workshop'/'tests'/'regression'/f'{name}.md').read_text(encoding='utf-8') for name in ('product_principles','data_model','reasoning','simulation')): errors.append('regression checklist placeholder remains')
    checks.append(('backlog and regression closure',errors))
    errors=[]; report=load(PROJECT/'reports'/'project_report_v1.1.json'); evidence=report.get('evidence_status',{})
    if evidence.get('implementation_result')!='verified' or evidence.get('post_implementation_analysis',{}).get('status')!='not_run' or evidence.get('post_implementation_simulation',{}).get('status')!='not_run' or evidence.get('gameplay_validation',{}).get('status')!='not_recorded' or evidence.get('performance_claim',{}).get('status')!='not_measured': errors.append('report evidence boundary is not honest')
    if [x.get('candidate_id') for x in cert.get('evidence_boundary',{}).get('needs_testing_candidates',[])] != ['cand-009','cand-010']: errors.append('needs-testing candidate state is incomplete')
    checks.append(('evidence honesty and candidate state',errors))
    errors=[]; renderer=render_module()
    if (PROJECT/'reports'/'sprint_1_certification.md').read_text(encoding='utf-8') != renderer.render_certification(cert): errors.append('certification Markdown differs from deterministic renderer output')
    if (PROJECT/'notes'/'backlog.md').read_text(encoding='utf-8') != renderer.render_backlog(backlog): errors.append('backlog Markdown differs from deterministic renderer output')
    checks.append(('deterministic closure rendering',errors))
    errors=[]
    commands=['validate_knowledge_layer.py','validate_candidate_card_facts.py','validate_recommendation_review.py','validate_decision_pipeline.py','validate_deck_versions.py','validate_project_reports.py']
    for command in commands:
        if subprocess.run([sys.executable,str(ROOT/'workshop'/'tests'/'validation'/command)],cwd=ROOT,capture_output=True).returncode: errors.append(f'layer validator {command} failed')
    env=os.environ.copy(); env.update({'WORKSHOP_RECOMMENDATION_JSON':'workshop/projects/the-myr-singularity/recommendations/rec-002.json','WORKSHOP_RECOMMENDATION_MD':'workshop/projects/the-myr-singularity/recommendations/rec-002.md'})
    if subprocess.run([sys.executable,str(ROOT/'workshop'/'tests'/'validation'/'validate_recommendation_schema.py')],cwd=ROOT,env=env,capture_output=True).returncode: errors.append('rec-002 validator failed')
    checks.append(('layer validator orchestration',errors))
    return emit(checks)
if __name__=='__main__': sys.exit(main())
