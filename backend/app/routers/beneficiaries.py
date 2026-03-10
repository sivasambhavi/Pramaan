import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.neo4j_client import get_session

logger = logging.getLogger(__name__)

router = APIRouter()

class BeneficiaryMetric(BaseModel):
    region_name: str
    scheme_name: str
    beneficiary_count: int
    description: str

@router.get("/booth/{booth_id}")
def get_booth_beneficiaries(booth_id: str):
    """
    Retrieve all beneficiaries linked to a specific booth.
    """
    query = """
    MATCH (b:Beneficiary)-[:LIVES_IN]->(r:Region {region_id: $booth_id})
    OPTIONAL MATCH (s:Scheme)-[:BENEFITS]->(b)
    RETURN 
        r.name AS region_name,
        COALESCE(s.name, 'Unknown Scheme') AS scheme_name,
        b.count AS beneficiary_count,
        b.description AS description
    ORDER BY b.count DESC
    """
    
    try:
        with get_session() as session:
            results = session.run(query, booth_id=booth_id).data()
        metrics = []
        for row in results:
            metrics.append(BeneficiaryMetric(**row))
        return {"booth_id": booth_id, "metrics": metrics}
    except Exception as e:
        logger.error(f"Error retrieving beneficiaries for {booth_id}: {e}")
        return {"error": str(e)}

@router.get("/scheme/{scheme_id}")
def get_scheme_beneficiaries(scheme_id: str):
    """
    Retrieve beneficiary counts per region for a specific scheme.
    """
    query = """
    MATCH (s:Scheme {scheme_id: $scheme_id})-[:BENEFITS]->(b:Beneficiary)-[:LIVES_IN]->(r:Region)
    RETURN 
        r.name AS region_name,
        s.name AS scheme_name,
        b.count AS beneficiary_count,
        b.description AS description
    ORDER BY b.count DESC
    """
    
    try:
        with get_session() as session:
            results = session.run(query, scheme_id=scheme_id).data()
        metrics = []
        for row in results:
            metrics.append(BeneficiaryMetric(**row))
        return {"scheme_id": scheme_id, "metrics": metrics}
    except Exception as e:
        logger.error(f"Error retrieving beneficiaries for scheme {scheme_id}: {e}")
        return {"error": str(e)}
