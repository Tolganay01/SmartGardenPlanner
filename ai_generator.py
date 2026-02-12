import os
import json
import time
import base64
import io
import datetime
import re
from google import genai
from google.genai import types
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class GardenAIGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if self.api_key:
            print(f"DEBUG: Using API Key: {self.api_key[:4]}...{self.api_key[-4:]}")
        else:
            print("DEBUG: No API Key found!")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = 'gemini-2.5-flash-lite'

    def _create_prompt(self, data):
        """CRITICAL INSTRUCTION FOR CROP DISTRIBUTION:
The user has already allocated specific square meters to each crop:
{crops_list}

Your "crop_distribution" MUST reflect these EXACT percentages based on total garden size.
Calculate: (crop area / total garden size) * 100 = percentage

DO NOT invent your own distribution. Use the user's actual area allocation."""
        crops_list = ", ".join([f"{c['name']} ({c['area']}sqm)" for c in data.get('crops', [])])
        
        # Yield guidelines by crop type
        yield_guidelines = """
IMPORTANT YIELD GUIDELINES - Use these realistic ranges PER 100 SQM and SCALE APPROPRIATELY for the actual garden size:
- Root vegetables (carrots, beets, radishes, parsnips): 80-120 kg
- Potatoes: 80-150 kg
- Tomatoes (field/open ground): 50-80 kg
- Tomatoes (greenhouse): 100-200 kg
- Cucumbers (field/open ground): 30-50 kg
- Cucumbers (greenhouse): 80-150 kg
- Leafy greens (lettuce, spinach, kale, chard): 15-25 kg
- Peppers (bell, chili): 30-50 kg
- Onions, garlic, leeks: 80-120 kg
- Beans (all types): 30-50 kg
- Peas: 20-40 kg
- Cabbage, broccoli, cauliflower: 80-120 kg
- Squash, zucchini: 50-80 kg
- Melons: 40-60 kg
- Corn: 20-30 kg
- Herbs (basil, parsley, cilantro): 5-10 kg

DO NOT EXCEED THESE RANGES. Be conservative and realistic, not optimistic.
SCALE the yield based on the actual garden size. If garden is 50 sqm, use half of these values.
"""
        
        return f"""
                ROLE: Professional Horticulture Consultant. You are an expert in vegetable gardening and crop yield prediction.

                CONTEXT: 
                - Location: {data.get('location')} climate
                - Garden size: {data.get('garden_size')} sqm
                - Soil type: {data.get('soil_type')}
                - Sunlight: {data.get('sunlight')}
                - Growing environment: {data.get('garden_type')}
                - Main goal: {data.get('main_goal')}
                - Include pest prevention tips: {data.get('pest_prevention')}

                CROPS TO PLAN: {crops_list}

                {yield_guidelines}

                TASK: Generate a comprehensive, data-driven garden plan for this specific location and garden size.

                IMPORTANT:
                1. Scale ALL yields to the ACTUAL garden size ({data.get('garden_size')} sqm), not per 100 sqm
                2. Be conservative - it's better to underestimate than overestimate
                3. Consider the specific growing environment (field vs greenhouse)
                4. Account for crop spacing and companion planting

                REQUIRED JSON STRUCTURE:
                {{
                "optimized_layout": {{
                    "crop_distribution": {{ "crop_name": "percentage%" }},
                    "spatial_arrangement": "Detailed description of how to arrange plants",
                    "companion_planting": ["list of good companions", "plants to avoid"],
                    "crop_rotation": "Rotation strategy for next season"
                }},
                "estimated_yield": {{ "crop_name": "range in kg/season (scaled to garden size)" }},
                "planting_periods": {{ "crop_name": "sowing month - harvest month" }},
                "smart_advice": {{
                    "irrigation": "Specific watering schedule and method",
                    "soil_management": "Fertilizer and amendment recommendations",
                    "local_risks": "Climate-specific challenges for {data.get('location')}",
                    "pest_prevention": "Organic pest control methods" if {data.get('pest_prevention')} else "Standard pest monitoring"
                }},
                "additional_tips": ["tip1", "tip2", "tip3"]
                }}
                """

    def generate_plan(self, garden_data):
        prompt = self._create_prompt(garden_data)
    
        for attempt in range(3):
            try:
                print(f"Using Gemini AI (Attempt {attempt+1})...")
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json',
                        temperature=0.7
                    )
                )
                
                plan_data = json.loads(response.text)
                
                # 🔴 FORCE CORRECT CROP DISTRIBUTION - ADD THIS RIGHT HERE
                total_size = garden_data['garden_size']
                correct_distribution = {}
                for crop in garden_data['crops']:
                    percentage = (crop['area'] / total_size) * 100
                    correct_distribution[crop['name']] = f"{percentage:.1f}%"
                
                # Override the AI's distribution with the correct one
                if 'optimized_layout' not in plan_data:
                    plan_data['optimized_layout'] = {}
                plan_data['optimized_layout']['crop_distribution'] = correct_distribution
                
                # Generate visuals based on the NEW plan_data
                plan_data['visualizations'] = self._generate_visualizations(garden_data, plan_data)
                plan_data['generated_at'] = datetime.datetime.now().isoformat()
                return plan_data

            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait_time = (attempt + 1) * 30
                    print(f"Rate limit hit. Retrying in {wait_time}s...")
                    if attempt < 2:
                        time.sleep(wait_time)
                        continue
                
                print(f"AI generation failed: {e}")
                return self._get_fallback_plan(garden_data, str(e))

    def _generate_visualizations(self, garden_data, plan_data):
        visuals = {}
        try:
            # HELPER FUNCTION: This is the important part using 're' 
            # It turns "60-100kg" into 80.0 so the chart doesn't show 60,000
            def parse_to_val(val_str):
                # Find all numbers (including decimals)
                nums = re.findall(r'\d+\.?\d*', str(val_str))
                if len(nums) >= 2:
                    return (float(nums[0]) + float(nums[1])) / 2
                return float(nums[0]) if nums else 0

            # 1. Pie Chart (Crop Distribution)
            plt.figure(figsize=(8, 6))
            dist = plan_data.get('optimized_layout', {}).get('crop_distribution', {})
            
            if dist:
                labels = list(dist.keys())
                sizes = [parse_to_val(v) for v in dist.values()]
            else:
                labels = [c['name'] for c in garden_data['crops']]
                sizes = [c['area'] for c in garden_data['crops']]
            
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#6A8D53', '#8FB377', '#A9C296', '#D1D9C0'])
            plt.title("Garden Area Distribution")
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            visuals['pie_chart'] = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close()

            # 2. Bar Chart (The 60,000kg Fix)
            plt.figure(figsize=(10, 6))
            yield_data = plan_data.get('estimated_yield', {})
            crops = list(yield_data.keys())
            # We use parse_to_val to get the average of the range
            yield_vals = [parse_to_val(v) for v in yield_data.values()]

            ax = plt.gca()
            ax.set_xticks(range(len(crops)))
            ax.set_xticklabels(crops, rotation=45, ha='right')
            
            plt.bar(range(len(crops)), yield_vals, color='#6A8D53')
            plt.ylabel("Estimated Yield (Average kg)")
            plt.title("Yield Projections")
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            visuals['bar_chart'] = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close()

        except Exception as e:
            print(f"Visualization error: {e}")
            visuals = {'pie_chart': None, 'bar_chart': None}
            
        return visuals

    def _get_fallback_plan(self, data, reason):
        # Scale yields based on actual garden size
        garden_size = data.get('garden_size', 100)
        scale_factor = garden_size / 100
        
        yield_estimates = {}
        for crop in data['crops']:
            crop_name = crop['name'].lower()
            if 'carrot' in crop_name or 'beet' in crop_name or 'radish' in crop_name or 'parsnip' in crop_name:
                yield_estimates[crop['name']] = f"{int(80 * scale_factor)}-{int(120 * scale_factor)} kg"
            elif 'potato' in crop_name:
                yield_estimates[crop['name']] = f"{int(80 * scale_factor)}-{int(150 * scale_factor)} kg"
            elif 'tomato' in crop_name:
                if data.get('garden_type') == 'greenhouse':
                    yield_estimates[crop['name']] = f"{int(100 * scale_factor)}-{int(200 * scale_factor)} kg"
                else:
                    yield_estimates[crop['name']] = f"{int(50 * scale_factor)}-{int(80 * scale_factor)} kg"
            elif 'cucumber' in crop_name:
                if data.get('garden_type') == 'greenhouse':
                    yield_estimates[crop['name']] = f"{int(80 * scale_factor)}-{int(150 * scale_factor)} kg"
                else:
                    yield_estimates[crop['name']] = f"{int(30 * scale_factor)}-{int(50 * scale_factor)} kg"
            elif 'lettuce' in crop_name or 'spinach' in crop_name or 'kale' in crop_name or 'chard' in crop_name:
                yield_estimates[crop['name']] = f"{int(15 * scale_factor)}-{int(25 * scale_factor)} kg"
            elif 'pepper' in crop_name:
                yield_estimates[crop['name']] = f"{int(30 * scale_factor)}-{int(50 * scale_factor)} kg"
            elif 'onion' in crop_name or 'garlic' in crop_name or 'leek' in crop_name:
                yield_estimates[crop['name']] = f"{int(80 * scale_factor)}-{int(120 * scale_factor)} kg"
            elif 'bean' in crop_name:
                yield_estimates[crop['name']] = f"{int(30 * scale_factor)}-{int(50 * scale_factor)} kg"
            elif 'pea' in crop_name:
                yield_estimates[crop['name']] = f"{int(20 * scale_factor)}-{int(40 * scale_factor)} kg"
            elif 'cabbage' in crop_name or 'broccoli' in crop_name or 'cauliflower' in crop_name:
                yield_estimates[crop['name']] = f"{int(80 * scale_factor)}-{int(120 * scale_factor)} kg"
            elif 'squash' in crop_name or 'zucchini' in crop_name:
                yield_estimates[crop['name']] = f"{int(50 * scale_factor)}-{int(80 * scale_factor)} kg"
            else:
                # Default for unknown crops
                yield_estimates[crop['name']] = f"{int(30 * scale_factor)}-{int(60 * scale_factor)} kg"
        
        return {
            "is_fallback": True,
            "optimized_layout": {
                "crop_distribution": {c['name']: f"{(c['area'] / data['garden_size'] * 100):.1f}%" for c in data['crops']},
                "spatial_arrangement": "Standard row-based planting recommended. Space plants according to seed packet instructions.",
                "companion_planting": ["Marigolds near tomatoes", "Basil near peppers", "Onions near carrots"],
                "crop_rotation": "Follow a 4-year rotation: legumes → leafy greens → fruiting crops → root crops"
            },
            "estimated_yield": yield_estimates,
            "planting_periods": {c['name']: "Plant after last frost, harvest before first frost" for c in data['crops']},
            "smart_advice": {
                "irrigation": "Water deeply 2-3 times per week, preferably in the morning.",
                "soil_management": "Add 2-3 inches of compost before planting. Mulch to retain moisture.",
                "local_risks": f"Monitor local weather forecasts for {data.get('location')}. Protect from unexpected frosts.",
                "pest_prevention": "Use row covers, practice crop rotation, encourage beneficial insects."
            },
            "additional_tips": [
                "Succession plant lettuce and radishes every 2 weeks for continuous harvest",
                "Install drip irrigation for water efficiency",
                "Keep a garden journal to track what works in your specific climate"
            ],
            "visualizations": {"pie_chart": None, "bar_chart": None}
        }