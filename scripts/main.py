import os
import glob
import json
import re
import importlib.util
from datetime import datetime

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def get_active_model():
    """اكتشاف أحدث وأسرع نموذج متاح لمفتاح الـ API تلقائياً"""
    if not HAS_GEMINI or not GEMINI_KEY:
        return None
    try:
        genai.configure(api_key=GEMINI_KEY)
        models = list(genai.list_models())
        
        # تفضيل نماذج Flash المتاحة للتوليد
        for m in models:
            if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower():
                return m.name
        # خطة بديلة: أول نموذج يدعم التوليد
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except Exception as e:
        print(f"⚠️ تعذر استعلام قائمة النماذج: {e}")
    return "models/gemini-1.5-flash"

ACTIVE_MODEL_NAME = get_active_model()

def validate_and_filter_with_ai(game_name, raw_items):
    """تطهير الأكواد بالذكاء الاصطناعي، الترتيب حسب التاريخ، والاقتصار على أحدث 12 كوداً"""
    if not raw_items:
        return []

    # في حال عدم تفعيل الـ AI: إزالة التكرار والاقتصار على أول 12 كوداً
    if not ACTIVE_MODEL_NAME:
        seen = set()
        codes = []
        for item in raw_items:
            c = item.get("code") if isinstance(item, dict) else str(item)
            if c and c not in seen:
                seen.add(c)
                codes.append(c)
        return codes[:12]

    try:
        model = genai.GenerativeModel(ACTIVE_MODEL_NAME)
        
        # تم تصحيح الأقواس المجعدة {{ }} لمنع خطأ Invalid format specifier
        prompt = f"""
        You are a professional promo code verification engine.
        Target Game: "{game_name}".
        Raw Data Collected from Multiple Sources: {json.dumps(raw_items)}

        Tasks:
        1. Remove English noise words, headers, expired labels, website UI text, and invalid formatting.
        2. Keep ONLY valid active promo/redeem codes for "{game_name}".
        3. Retain or estimate the publication date ('YYYY-MM-DD') for each valid code.

        Output Requirement:
        Return ONLY a strict JSON array of objects with keys "code" and "date".
        Example: [{{"code": "EXAMPLE123", "date": "2026-09-15"}}]
        """

        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        response = model.generate_content(prompt, generation_config=generation_config)

        if response.text:
            text_cleaned = re.sub(r'^```json\s*|^```\s*|\s*```$', '', response.text.strip(), flags=re.MULTILINE)
            parsed = json.loads(text_cleaned)
            
            valid_list = []
            if isinstance(parsed, list):
                valid_list = parsed
            elif isinstance(parsed, dict):
                for val in parsed.values():
                    if isinstance(val, list):
                        valid_list = val
                        break

            # دالة ترتيب زمني محصنة ضد الأخطاء
            def get_sort_key(item):
                if isinstance(item, dict):
                    d_str = item.get('date', '2000-01-01')
                    try:
                        return datetime.strptime(d_str, '%Y-%m-%d')
                    except Exception:
                        pass
                return datetime(2000, 1, 1)

            valid_list.sort(key=get_sort_key, reverse=True)

            # إزالة التكرارات بعد الترتيب الزمني
            final_codes = []
            seen = set()
            for item in valid_list:
                c = item.get('code') if isinstance(item, dict) else str(item)
                if c and c not in seen:
                    seen.add(c)
                    final_codes.append(c)

            # تطبيق شرط الـ 12 كود
            return final_codes[:12]

    except Exception as e:
        print(f"⚠️ خطأ أثناء الفحص بالذكاء الاصطناعي لـ {game_name}: {e}")

    # خطة التراجع عند حدوث أي خطأ في استجابة AI
    seen = set()
    codes = []
    for item in raw_items:
        c = item.get("code") if isinstance(item, dict) else str(item)
        if c and c not in seen:
            seen.add(c)
            codes.append(c)
    return codes[:12]

def run_main_engine():
    final_database = {}
    game_files = sorted(glob.glob("games/*.py"))
    
    print(f"🚀 بدء معالجة {len(game_files)} لعبة داخل مجلد games/...")
    if ACTIVE_MODEL_NAME:
        print(f"🤖 الذكاء الاصطناعي النشط: {ACTIVE_MODEL_NAME}")

    for file_path in game_files:
        module_name = os.path.basename(file_path).replace(".py", "")
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "get_codes"):
                game_name, raw_items = module.get_codes()
                print(f"📥 {game_name}: تم جلب {len(raw_items)} عنصر خام من كافة المصادر")
                
                clean_codes = validate_and_filter_with_ai(game_name, raw_items)
                final_database[game_name] = clean_codes
                print(f"✅ {game_name}: اعتماد {len(clean_codes)} كود نهائي")
        except Exception as e:
            print(f"❌ خطأ أثناء تنفيذ {module_name}: {e}")

    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(final_database, f, ensure_ascii=False, indent=2)

    print("🎉 تم التحديث بنجاح وحفظ البيانات في codes.json")

if __name__ == "__main__":
    run_main_engine()

