from ..app.database import db_session
from ..models.result import Result

def add(camera_pos, datetime, product_id):
    result = Result(camera_pos, datetime, product_id)
        
    db_session.add(result)
        
    db_session.commit()
        
    return result.id

def get_results_by_product(product_id):
    references = Result.query.filter(Result.product_id == product_id).order_by(Result.datetime.desc()).limit(2)
    sorted_references = sorted(references, key=lambda x: x.camera_pos, reverse=False)
    return sorted_references
    