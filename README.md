# s_agent 🤖 — وكيل برمجة عربي، سريع وعملي ومتكامل

مستوحى من [alphacode](https://github.com/dragonked2/alphacode) — **بايثون خالص، الأساس stdlib فقط** (صفر اعتماديات إجبارية) + إضافتان اختياريتان للتحكم الحقيقي.

## لماذا أسرع؟
- **صفر اعتماديات**: يعمل فورًا على أي Python 3.9+.
- **تنفيذ متوازٍ**: دفعات الأدوات تعمل معًا (`ThreadPoolExecutor`) بدل التسلسل.
- **محرك محلي**: يعمل **بدون API key وبدون إنترنت** (تخطيط heuristic فوري)، ومع LLM عند توفره.
- **سياق محدود**: ملخصات قصيرة + حد 12 خطوة + دفعات من 4.

## المزايا (مقابل alphacode)
| alphacode | s_agent |
|---|---|
| Rust + 40 أداة + Firefox + Desktop | Python + 14 أداة (ملفات/بحث/تنفيذ/ويب/ذاكرة/مهام + **متصفح حقيقي + سطح مكتب**) |
| Swarm mode | ✅ `/swarm` متوازي |
| Sessions | ✅ JSONL مستمرة |
| Multi-provider + free lane | ✅ OpenAI-compat (OpenAI/Gemini/DeepSeek/OpenRouter/Ollama/LMStudio) + `local` المجاني |
| TUI | ✅ REPL عربي + أوامر `/diff /sessions /doctor` |
| Safety | ✅ حظر مسارات/أوامر مدمرة + تأكيد الوضع الآمن |

## التثبيت (Windows)
```powershell
cd s_agent
pip install -e .
python -m s_agent doctor
```

## الاستخدام
```bash
# تفاعلي (عربي)
python -m s_agent
s_agent> اشرح هذا المشروع

# مهمة واحدة (بدون تأكيد)
python -m s_agent run "ابحث عن الدالة main" --yes

# وضع السرب (4 وكلاء متوازيين)
python -m s_agent swarm "راجع المشروع معماريًا وأمنيًا" --yes

# ربط نموذجك (اختياري — بدونه يعمل المحلي)
python -m s_agent login
# أو: $env:OPENAI_API_KEY="..." ; ثم login --provider openai
# محلي: Ollama → login --provider ollama

# أوامر داخل الجلسة
/swarm <هدف>  /diff  /sessions  /doctor  /exit
/browser open https://example.com  /browser shot  /desktop shot
```

## التحكم الحقيقي (playwright / pyautogui)
```bash
# المتصفح الحقيقي — Firefox أولًا (مثل alphacode)
pip install playwright
python -m playwright install firefox
python -m s_agent browser status
python -m s_agent browser open --url https://example.com
python -m s_agent run "افتح https://example.com ولخص محتواه" --yes
# إجراءات: open|text|click|fill|type|press|screenshot|close
python -m s_agent browser click --selector "#login" --url https://example.com

# سطح المكتب — PyAutoGUI (FAILSAFE: الفأرة للزاوية العلوية للإيقاف)
pip install pyautogui pillow
python -m s_agent desktop status
python -m s_agent desktop screenshot
python -m s_agent desktop click --x 500 --y 300
# إجراءات: status|size|screenshot|move|click|type|press|hotkey|scroll|locate|windows
```
> بدونهما يعمل كل شيء آخر (12 أداة stdlib) — `doctor` يخبرك بالناقص بدل أن يكسر.

## السرعة والكفاءة
- `run_batch(parallel=True)`: دفعات متوازية حتى 8 خيوط.
- `local_plan`: قواعد regex عربية/إنجليزية → أدوات مباشرة بلا انتظار شبكة (بما فيها توجيه المتصفح/سطح المكتب).
- استهلاك الأساس ≈ ~20MB (مقابل ~28MB لـ alphacode و~300MB لأدوات Node)؛ playwright/pyautogui تُحمّل كسولًا فقط عند الاستدعاء.

## الحدود بصراحة
- المتصفح headless افتراضيًا (أسرع) — أضف `--headed` لنافذة مرئية؛ الجلسات الحقيقية المسجّلة الدخول تحتاج `firefox` النظامي لا headless أحيانًا.
- سطح المكتب إحداثيات/صور صريحة + FAILSAFE — لا تخمين عشوائي للنقر (أمان).
