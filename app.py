from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from nlp.hybrid_extractor import hybrid_extract
from usda.fooddata_api import get_nutrition_for_item, _normalize_macros_map
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nutri-Vision Text Service", version="1.0.0")

class TextIn(BaseModel):
    description: str

class MacroInfo(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

class FoodItem(BaseModel):
    ingredient: str
    quantity: float
    unit: str
    macros: MacroInfo
    usda_match_score: float = None
    note: str = None

class AnalysisResult(BaseModel):
    input: str
    items: list[FoodItem]
    totals: MacroInfo

@app.get("/")
def read_root():
    return {
        "message": "Nutri-Vision Text Service",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze-text",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

def _format_item_nutrition(item, nutrition_result):
    """
    Format nutrition information for a single item.
    Returns normalized macros dict with calories, protein_g, carbs_g, fat_g
    """
    if nutrition_result.get("error"):
        return {
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0
        }
    
    # Get macros from the nutrition result
    macros = nutrition_result.get("macros", {})
    
    # Ensure all required keys exist and normalize
    normalized = _normalize_macros_map(macros)
    
    return normalized

@app.post("/analyze-text", response_model=AnalysisResult)
def analyze_text(payload: TextIn):
    """
    Analyze text input to extract food items and their nutritional information
    """
    try:
        text = payload.description.strip()
        
        if not text:
            raise HTTPException(status_code=400, detail="Description cannot be empty")
        
        logger.info(f"Analyzing text: '{text}'")
        
        # Extract food items using hybrid approach
        items = hybrid_extract(text)
        
        if not items:
            logger.warning(f"No food items extracted from: '{text}'")
            return AnalysisResult(
                input=text,
                items=[],
                totals=MacroInfo(calories=0.0, protein_g=0.0, carbs_g=0.0, fat_g=0.0)
            )
        
        logger.info(f"Extracted {len(items)} items: {[item['ingredient'] for item in items]}")
        
        items_out = []
        totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
        
        for item in items:
            try:
                logger.info(f"Getting nutrition for: {item}")
                
                # Get nutrition information
                nutrition_result = get_nutrition_for_item(item)
                
                if nutrition_result.get("error"):
                    logger.warning(f"Nutrition error for {item['ingredient']}: {nutrition_result['error']}")
                    macros = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
                    
                    items_out.append(FoodItem(
                        ingredient=item.get("ingredient", "unknown"),
                        quantity=item.get("quantity", 1.0),
                        unit=item.get("unit", "serving"),
                        macros=MacroInfo(**macros),
                        note=nutrition_result.get("error")
                    ))
                    continue
                
                # Format macros
                macros = _format_item_nutrition(item, nutrition_result)
                
                # Accumulate totals
                for key in totals:
                    totals[key] += macros.get(key, 0.0)
                
                # Add to output
                items_out.append(FoodItem(
                    ingredient=item.get("ingredient", "unknown"),
                    quantity=item.get("quantity", 1.0),
                    unit=item.get("unit", "serving"),
                    macros=MacroInfo(**macros),
                    usda_match_score=nutrition_result.get("score")
                ))
                
                logger.info(f"Successfully processed {item['ingredient']}: {macros}")
                
            except Exception as e:
                logger.error(f"Error processing item {item}: {str(e)}")
                
                # Add item with zero macros and error note
                macros = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
                items_out.append(FoodItem(
                    ingredient=item.get("ingredient", "unknown"),
                    quantity=item.get("quantity", 1.0),
                    unit=item.get("unit", "serving"),
                    macros=MacroInfo(**macros),
                    note=f"Processing error: {str(e)}"
                ))
        
        # Round totals to 2 decimal places
        totals = {k: round(v, 2) for k, v in totals.items()}
        
        logger.info(f"Final totals: {totals}")
        
        return AnalysisResult(
            input=text,
            items=items_out,
            totals=MacroInfo(**totals)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/test-extraction")
def test_extraction(payload: TextIn):
    """
    Test endpoint to see raw extraction results without USDA lookup
    """
    text = payload.description.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    
    items = hybrid_extract(text)
    
    return {
        "input": text,
        "extracted_items": items,
        "count": len(items)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)