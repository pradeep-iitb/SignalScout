from fastapi import APIRouter, HTTPException
from backend.services.storage import storage

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

@router.get("/{company_id}")
async def get_candidate_details(company_id: str):
    """
    Returns complete candidate dossier: company profile, verified founders,
    discovered signals, hypotheses, contradictions, and investment memo.
    """
    # Look through active and historical investigations
    for inv in storage.list_all():
        ranked = inv.get("ranked_candidates", [])
        memos = inv.get("investment_memos", [])
        
        target_cand = next((c for c in ranked if c.get("company_id") == company_id), None)
        target_memo = next((m for m in memos if m.get("company_id") == company_id), None)

        if target_cand or target_memo:
            evidence = storage.get_evidence_for_company(company_id)
            return {
                "company_id": company_id,
                "candidate": target_cand,
                "memo": target_memo,
                "evidence": evidence
            }

    raise HTTPException(status_code=404, detail="Candidate not found")

@router.get("/{company_id}/evidence")
async def get_candidate_evidence(company_id: str):
    """
    Returns full verifiable evidence trail for an entity:
    Claim -> Evidence Text -> Source Type -> URL/Reference -> Confidence
    """
    evidence = storage.get_evidence_for_company(company_id)
    return {
        "company_id": company_id,
        "evidence_count": len(evidence),
        "evidence": evidence
    }
