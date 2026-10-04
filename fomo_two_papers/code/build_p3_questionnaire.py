# -*- coding: utf-8 -*-
import re, os
from docbuilder import Doc, fa
from docbuilder_en import DocEN
import paper3_instrument as P
OUT = os.path.join("..", "paper3"); os.makedirs(OUT, exist_ok=True)
plain = lambda s: s.replace("//", "")
def cite(keys):
    out = []
    for k in keys:
        m = re.match(r"([^,]+),", P.REF[k]); y = re.search(r"\((\d{4})\)", P.REF[k]).group(1); out.append(f"{m.group(1)} ({y})")
    return "; ".join(out)
CLS_FA = {P.RB: "پژوهش‌محور (اقتباس‌شده)", P.RM: "محقق‌ساخته (برگرفته از نظریه)", P.MIX: "ترکیبی: بخشی اقتباس‌شده، بخشی محقق‌ساخته"}
# ---------------------------------------------------------------- English
d = DocEN(); d.title("Questionnaire for Paper 3: Generative-AI Use, Competence Illusion and Investment Decision Quality")
d.para("**Status.** Draft instrument for a planned survey of individual investors. None of the multi-item scales below is a published, validated instrument in this exact form. Each variable is classified as //research-based (adapted)//, //researcher-made (theory-derived)// or //mixed//; the reference list for each variable gives the sources of the construct definition and (where applicable) of the item wording. Before real data collection, run the validation protocol in Section 3. Check every DOI in Crossref before citing.", indent=False)
d.heading("1. Overview: origin of each scale")
rows = [(v["code"], v["name"], str(len(v["items"])), v["cls"], cite(v["refs"])) for v in P.VARS]
d.table("Table 1. Variables, origin classification and principal references", ["Code", "Construct", "Items", "Origin", "References"], rows, widths=[600, 2700, 600, 2000, 3400])
d.para("Reading guide. //Research-based// = the construct and its item logic come from a published instrument or an established measurement method and were adapted (translated, re-worded, shortened) without changing the construct. //Researcher-made// = no published scale fits the construct; items were written by the authors from theory and require full validation. All Likert items are 5-point; higher scores mean more of the construct. Latent variables are never summed or averaged: every item is attached to its own latent variable in the SEM.", indent=False)
d.heading("2. Instrument by variable")
for i, v in enumerate(P.VARS, 1):
    d.heading(f"2.{i} {v['name']} ({v['code']})", 2)
    d.para(f"**Origin:** {v['cls']}.  **Response format:** {v['scale']}.  **Role in the model:** {v['role']}.", indent=False)
    d.para(f"**Basis and status.** {v['why']}", indent=False)
    d.table(f"Table 2.{i}. Items of {v['code']}", ["Code", "Item"], [(c, e) for c, e, _ in v["items"]], widths=[800, 8500])
    d.para("**References for this variable**", indent=False, after=30)
    for k in v["refs"]: d.reference(P.REF[k])
d.heading("2.10 Demographics and descriptive questions", 2)
d.table("Table 2.10. Demographic items", ["Code", "Item"], [(c, e) for c, e, _ in P.DEMO], widths=[800, 8500])
d.heading("3. Validation protocol before real data collection")
for t in ["**Content validity.** Panel of 10–12 experts (behavioural finance, accounting, AI/HCI, psychometrics): Lawshe's CVR (minimum 0.62 for 10 experts), item-level and scale-level CVI (I-CVI ≥ 0.78; S-CVI/Ave ≥ 0.90) (Lawshe, 1975; Polit & Beck, 2006).",
          "**Translation.** For items written in Persian and reported in English (or vice versa): forward–backward translation and reconciliation (Brislin, 1970).",
          "**Cognitive pretest and pilot.** 8–10 cognitive interviews, then a pilot of 60–100 investors: item distributions, corrected item–total correlations, α/ω, EFA with parallel analysis; item difficulty and discrimination (KR-20, point-biserial) for the knowledge test (Boateng et al., 2018).",
          "**Main study.** CFA of the full measurement model with fit judged jointly (CFI/TLI, RMSEA, SRMR; Hu & Bentler, 1999), CR/AVE (Fornell & Larcker, 1981), HTMT < 0.85 (Henseler et al., 2015), common-method checks (Podsakoff et al., 2003). Collect the knowledge test and the predicted score in the same session, with the predictions made //before// feedback.",
          "**Procedural remedies.** Place the objective test before the attitude scales; randomise item order within blocks; do not offer feedback on the test score until the end; include attention checks; record device and completion time."]:
    d.para(t, indent=False)
d.heading("4. Scoring")
for t in ["Latent constructs (GUI, PCA, UR, VER, AIL, IDQ): no composite scores are computed; each item is a manifest indicator of its latent variable. Descriptive means are reported only for reference.",
          "Knowledge test: sum of correct answers (0–8) for the calibration gap; standardized (z) score FKz is the observed moderator in the SEM. KR-20 is reported.",
          "Calibration gap: CG = C1 − test score (positive = overestimation); over-placement CP = C2 − actual percentile rank. In the SEM, CG is standardized (CGz) and modelled as a second 'illusion' mediator beside PCA.",
          "Vignette error score VIGERR = number of incorrect AI statements (V1, V3) that the respondent accepts (0–2); verification behaviour can be scored from 'verify first' answers (0–4)."]:
    d.para(t, indent=False)
d.heading("5. All references used in this document")
used = sorted({k for v in P.VARS for k in v["refs"]} | set(P.VALID), key=lambda k: P.REF[k])
for k in used: d.reference(P.REF[k])
d.save(os.path.join(OUT, "Paper3_Questionnaire_EN.docx"), title="Paper 3 Questionnaire (EN)")
# ---------------------------------------------------------------- Persian
f = Doc(body_pt=12); f.title("پرسشنامهٔ مقالهٔ سوم: استفاده از هوش مصنوعی مولد، توهم شایستگی و کیفیت تصمیم سرمایه‌گذاری")
f.para("**وضعیت.** پیش‌نویس ابزار برای پیمایش سرمایه‌گذاران حقیقی. هیچ‌یک از مقیاس‌های چندگویه‌ای زیر، به همین شکل، ابزار منتشرشدهٔ اعتبارسنجی‌شده نیست. هر متغیر به یکی از دسته‌های «پژوهش‌محور (اقتباس‌شده)»، «محقق‌ساخته (برگرفته از نظریه)» یا «ترکیبی» تعلق دارد و منابع هر متغیر در کنار آن آمده است. پیش از گردآوری دادهٔ واقعی پروتکل اعتبارسنجی بخش ۳ را اجرا کنید و DOIها را در Crossref بررسی کنید.", indent=False)
f.heading("۱) نمای کلی: منشأ هر مقیاس")
f.table("جدول ۱. متغیرها، نوع منشأ و منابع اصلی", ["کد", "سازه", "گویه", "منشأ", "منابع"], [(v["code"], v["fa"], str(len(v["items"])), CLS_FA[v["cls"]], cite(v["refs"])) for v in P.VARS], widths=[700, 2300, 600, 2000, 3400], size=20)
f.para("**راهنما.** «پژوهش‌محور» یعنی سازه و منطق گویه‌ها از ابزار یا روش منتشرشده می‌آید و فقط بازنویسی/ترجمه/اختصار شده است. «محقق‌ساخته» یعنی مقیاس منتشرشدهٔ مناسبی وجود ندارد، گویه‌ها از نظریه نوشته شده‌اند و نیازمند اعتبارسنجی کامل‌اند. تمام گویه‌های لیکرت ۵‌درجه‌ای‌اند و هیچ نمرهٔ ترکیبی/میانگین گویه‌ها ساخته نمی‌شود؛ هر گویه به متغیر پنهان خود وصل است.", indent=False)
f.heading("۲) ابزار به تفکیک متغیر")
for i, v in enumerate(P.VARS, 1):
    f.heading(f"۲‑{i}) {v['fa']} ({v['code']})", 2)
    f.para(f"**منشأ:** {CLS_FA[v['cls']]}.  **مقیاس پاسخ:** {v['scale']}.", indent=False)
    f.table(f"جدول ۲‑{i}. گویه‌های {v['code']}", ["کد", "گویه"], [(c, p) for c, _, p in v["items"]], widths=[900, 8100], size=22)
    f.para("**منابع این متغیر**", indent=False, after=30)
    for k in v["refs"]: f.reference(plain(P.REF[k]), latin=True)
f.heading("۲‑۱۰) پرسش‌های جمعیت‌شناختی", 2)
f.table("جدول ۲‑۱۰. پرسش‌های جمعیت‌شناختی", ["کد", "پرسش"], [(c, p) for c, _, p in P.DEMO], widths=[900, 8100], size=22)
f.heading("۳) پروتکل اعتبارسنجی پیش از گردآوری داده")
for t in ["**روایی محتوا:** پنل ۱۰ تا ۱۲ خبره؛ CVR لاوشه (حداقل ۰٫۶۲ برای ۱۰ خبره) و CVI سطح گویه (≥ ۰٫۷۸) و سطح مقیاس (≥ ۰٫۹۰).",
          "**ترجمه:** ترجمهٔ رفت‌وبرگشت (Brislin, 1970) برای گویه‌هایی که در دو زبان گزارش می‌شوند.",
          "**پیش‌آزمون و مطالعهٔ مقدماتی:** ۸ تا ۱۰ مصاحبهٔ شناختی و سپس ۶۰ تا ۱۰۰ سرمایه‌گذار: توزیع گویه‌ها، همبستگی گویه‑کل، آلفا/امگا، تحلیل عاملی اکتشافی با تحلیل موازی؛ دشواری و تمایز سؤالات آزمون دانش (KR‑20).",
          "**مطالعهٔ اصلی:** CFA، شاخص‌های برازش به‌صورت توأمان، CR/AVE، HTMT < ۰٫۸۵ و بررسی سوگیری روش مشترک؛ پیش‌بینی نمره پیش از دریافت هرگونه بازخورد انجام شود.",
          "**تمهیدات رویه‌ای:** آزمون عینی پیش از مقیاس‌های نگرشی، تصادفی‌سازی ترتیب گویه‌ها در بلوک، سؤال توجه و ثبت زمان تکمیل."]:
    f.para(t, indent=False)
f.heading("۴) نمره‌گذاری")
for t in ["سازه‌های پنهان (GUI، PCA، UR، VER، AIL، IDQ): هیچ نمرهٔ ترکیبی ساخته نمی‌شود؛ هر گویه نشانگر متغیر پنهان خود است.",
          "آزمون دانش: مجموع پاسخ‌های درست (۰ تا ۸)؛ نمرهٔ استاندارد FKz در مدل به‌عنوان تعدیل‌گر وارد می‌شود و KR‑20 گزارش می‌شود.",
          "شکاف کالیبراسیون: CG = C1 − نمرهٔ آزمون (مثبت = بیش‌برآورد)؛ بیش‌جایگذاری CP = C2 − رتبهٔ واقعی. در مدل، CG استاندارد (CGz) و به‌عنوان میانجی دوم «توهم» کنار PCA قرار می‌گیرد.",
          "خطای وینیت VIGERR = تعداد گزاره‌های نادرست (V1 و V3) که پذیرفته می‌شود (۰ تا ۲)."]:
    f.para(t, indent=False)
f.save(os.path.join(OUT, "Paper3_Questionnaire_FA.docx"))
print("ok")
