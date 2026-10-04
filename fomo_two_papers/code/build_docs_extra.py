# -*- coding: utf-8 -*-
"""پرسشنامهٔ هر مقاله، چکیدهٔ گسترده (فارسی/لاتین) و فرم‌های ارسال (DOCX)"""
import os, sys, json
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from docbuilder import Doc, fa, num, S
import instrument as I
from refs import LAT, apa_latin
D = os.path.join(H, "..", "deliverables")
F2 = lambda x: fa(f"{x:.2f}"); F3 = lambda x: fa(f"{x:.3f}")
TITLES = {
 1: ("اثر مواجهه با محتوای سرمایه‌گذاری شبکه‌های اجتماعی بر کیفیت تصمیم سرمایه‌گذاران حقیقی بورس تهران: نقش میانجی متوالی فومو و رفتار توده‌وار و نقش تعدیل‌گر استفاده از اطلاعات حسابداری",
     "The Effect of Exposure to Social-Media Investment Content on the Decision Quality of Individual Investors in the Tehran Stock Exchange: Sequential Mediation of FOMO and Herding and Moderation by Accounting Information Use"),
 2: ("پیش‌برنده‌ها و پیامدهای فومو در رقابت منابع اطلاعاتی سرمایه‌گذاران حقیقی: ناوردایی اندازه‌گیری و تفاوت مسیرها بر پایهٔ تجربهٔ زیان در ریزش بورس، با تحلیل تکمیلی یادگیری ماشین",
     "Antecedents and Consequences of FOMO in the Competition Between Information Sources Among Individual Investors: Measurement Invariance and Path Differences by Loss Experience in the Stock-Market Crash, with Supplementary Machine Learning"),
}
def ph(t): return f"=={t}=="

# ------------------------------------------------------------------ پرسشنامه
def questionnaire(p):
    R = json.load(open(os.path.join(H, "..", f"paper{p}", "output", f"results_paper{p}.json"), encoding="utf-8"))
    d = Doc(body_pt=12); cons = I.PAPER[p]; nitems = sum(len(I.ITEMS[k]) for k in cons)
    d.title(f"پرسشنامهٔ پژوهش — مقالهٔ {'اول' if p == 1 else 'دوم'}")
    d.para(TITLES[p][0], jc="center", indent=False, size=24, bold=True, after=120)
    d.heading("سرمایه‌گذار گرامی")
    d.para("این پرسشنامه برای یک پژوهش دانشگاهی دربارهٔ تصمیم‌های سرمایه‌گذاران حقیقی در بازار سرمایهٔ ایران تهیه شده است. شرکت در پژوهش اختیاری است و پاسخ‌ها **کاملاً بی‌نام** گردآوری و فقط به‌صورت آماری و گروهی تحلیل می‌شود. پاسخ درست یا نادرست وجود ندارد؛ لطفاً مطابق رفتار واقعی خود در **۱۲ ماه گذشته** پاسخ دهید. تکمیل پرسشنامه حدود ۱۰ دقیقه زمان می‌برد. با تکمیل و ارسال پرسشنامه، رضایت آگاهانهٔ خود را برای استفادهٔ پژوهشی از پاسخ‌ها اعلام می‌کنید.")
    d.para("**شرط ورود:** حداقل یک سال سابقهٔ معاملهٔ مستقل در بازار سهام (بورس یا فرابورس) به‌صورت حقیقی. **تماس با پژوهشگر:** " + ph("ایمیل پژوهشگر"), indent=False)
    d.heading("بخش الف) اطلاعات عمومی")
    rows = [[c, q, o] for c, v, q, t, cod, o in I.DEMO if c in I.DEMO_PAPER[p]]
    d.table("جدول الف. سؤال‌های جمعیت‌شناختی", ["کد", "سؤال", "گزینه‌ها / پاسخ"], rows, widths=[700, 4300, 4000], size=22)
    d.heading("بخش ب) گویه‌های اصلی")
    d.para("**مقیاس پاسخ (لیکرت ۵ درجه‌ای):** ۱ = کاملاً مخالفم | ۲ = مخالفم | ۳ = نظری ندارم | ۴ = موافقم | ۵ = کاملاً موافقم. برای هر گویه فقط یک گزینه را علامت بزنید.", indent=False)
    n = 0
    for k in cons:
        n += 1
        d.heading(f"{fa(str(n))}) {I.CONSTRUCTS[k][0]} — {I.CONSTRUCTS[k][1]} ({k})", 2)
        rows = [[c, t, "☐", "☐", "☐", "☐", "☐"] for c, t in I.ITEMS[k]]
        d.table(f"جدول {fa(str(n))}. گویه‌های سازهٔ {k}", ["کد", "گویه", "۱", "۲", "۳", "۴", "۵"], rows, widths=[800, 5372, 580, 580, 580, 580, 580], size=22)
    d.para("**گویهٔ کنترل دقت (نسخهٔ آنلاین؛ در میان گویه‌ها قرار می‌گیرد):** «برای نشان‌دادن دقت، در این ردیف گزینهٔ ۴ را انتخاب کنید.» پاسخ‌دهندهٔ ناموفق از تحلیل کنار گذاشته می‌شود.", indent=False)
    d.para("با سپاس از وقتی که گذاشتید.", jc="center", indent=False)
    d.page_break()
    # ---- راهنمای پژوهشگر
    d.title("پیوست پژوهشگر: منابع، نمره‌دهی و اعتبارسنجی (در نسخهٔ توزیع‌شده حذف شود)")
    d.heading("۱. مبنای نظری و منبع هر سازه")
    rows = []
    for k in cons:
        c = I.CONSTRUCTS[k]; src = "؛ ".join(LAT[x][0].split("(")[0].strip().rstrip(",") + " (" + LAT[x][0].split("(")[1][:4] + ")" for x in c[2])
        rows.append([f"{c[0]} ({k})", fa(str(len(I.ITEMS[k]))), src, c[3]])
    d.table("جدول ۱. منبع و وضعیت گویه‌ها", ["سازه", "گویه", "منابع مبنا", "وضعیت"], rows, widths=[2400, 600, 3600, 2400], size=20)
    d.para("**هشدار روش‌شناختی:** هیچ‌یک از گویه‌ها نسخهٔ استانداردشدهٔ فارسی نیست؛ همه از مقیاس‌های بین‌المللی بازنویسی یا بر پایهٔ تعریف نظری سازه توسط پژوهشگر ساخته شده‌اند و پیش از جمع‌آوری داده‌ٔ واقعی باید اعتبارسنجی شوند (بخش ۴).", indent=False)
    d.heading("۲. راهنمای نمره‌دهی")
    d.para("**کدگذاری پاسخ‌ها:** گزینه‌ها به ترتیب ۱ تا ۵ کد می‌شوند. هیچ گویهٔ معکوسی وجود ندارد، بنابراین بازکدگذاری لازم نیست. **نمرهٔ سازه** = میانگین حسابی گویه‌های آن سازه (دامنه ۱ تا ۵)؛ نمرهٔ بالاتر یعنی شدت بیشتر سازه (در کیفیت تصمیم: کیفیت بهتر). **داده‌های گم‌شده:** اگر دست‌کم ۸۰٪ گویه‌های یک سازه پاسخ داده شده باشد، میانگین گویه‌های پاسخ‌داده‌شده محاسبه می‌شود، وگرنه نمرهٔ آن سازه گم‌شده است.", indent=False)
    rows = []
    for k in cons:
        cs = [c for c, _ in I.ITEMS[k]]; mn = len(cs)
        rows.append([f"{I.CONSTRUCTS[k][0]} ({k})", "، ".join(cs), f"میانگین {fa(str(mn))} گویه", f"{fa(str(mn))} تا {fa(str(5*mn))}", "۱ تا ۵"])
    d.table("جدول ۲. فرمول نمره‌دهی", ["سازه", "گویه‌ها", "فرمول", "جمع خام", "نمرهٔ میانگین"], rows, widths=[2300, 2700, 1500, 1300, 1200], size=20)
    d.para("**تفسیر نمرهٔ میانگین (پیشنهادی):** ۱ تا ۲٫۳۳ = پایین؛ ۲٫۳۴ تا ۳٫۶۷ = متوسط؛ ۳٫۶۸ تا ۵ = بالا. **مثال محاسبه:** اگر پاسخ‌های یک نفر به گویه‌های FOMO1 تا FOMO6 برابر ۴، ۵، ۳، ۴، ۴ و ۵ باشد، نمرهٔ فومو = (۴+۵+۳+۴+۴+۵) ÷ ۶ = ۴٫۱۷ (سطح بالا). **متغیرهای دیگر:** جنسیت (۱ = مرد، ۰ = زن)، تحصیلات (۱ تا ۴)" + ("، تجربهٔ زیان LE (۰ = خیر، ۱ = بله)" if p == 2 else "") + ".", indent=False)
    d.heading("۳. شاخص‌های مورد انتظار پایایی و روایی")
    rel = R["rel"]
    rows = [[f"{I.CONSTRUCTS[k][0]} ({k})", F3(rel[k]["alpha"]), F3(rel[k]["cr"]), F3(rel[k]["ave"])] for k in cons]
    d.table("جدول ۳. پایایی و روایی همگرا در داده‌ٔ شبیه‌سازی‌شده (مرجع مقایسه؛ نه نتیجهٔ تجربی)", ["سازه", "آلفا", "CR", "AVE"], rows, widths=[4600, 1500, 1500, 1500], size=22,
            note="آستانه‌ها: آلفا و CR ≥ ۰٫۷۰؛ AVE ≥ ۰٫۵۰ (فورنل و لارکر)؛ HTMT < ۰٫۸۵ (هنسلر و همکاران)؛ بار عاملی استاندارد ≥ ۰٫۵۰؛ برازش: CFI و TLI ≥ ۰٫۹۵، RMSEA ≤ ۰٫۰۶، SRMR ≤ ۰٫۰۸ (هو و بنتلر).")
    d.heading("۴. پروتکل اعتبارسنجی پیش از گردآوری")
    steps = [
     "روایی صوری: ارزیابی خوانایی و وضوح گویه‌ها با ۱۰ تا ۱۵ سرمایه‌گذار فعال؛ اصلاح واژه‌های مبهم.",
     "روایی محتوا (کمّی): ارزیابی ۸ تا ۱۰ متخصص (حسابداری، مالی رفتاری، روان‌شناسی). برای هر گویه نسبت روایی محتوا (CVR) به روش لاوشه: CVR = (n_e − N/2) ÷ (N/2). حداقل مقدار پذیرفتنی برای N = ۸، ۱۰، ۱۲ و ۱۵ به ترتیب ۰٫۷۵، ۰٫۶۲، ۰٫۵۶ و ۰٫۴۹ است. شاخص روایی محتوا (CVI) برای ارتباط گویه (مقیاس ۱ تا ۴؛ نسبت امتیاز ۳ و ۴)؛ پذیرش I-CVI ≥ ۰٫۷۸ و S-CVI/Ave ≥ ۰٫۹۰ (پولیت و بک).",
     "ترجمه و ترجمهٔ معکوس برای گویه‌های برگرفته از مقیاس‌های انگلیسی (بریسلین)؛ مقایسهٔ دو مترجم مستقل و رفع اختلاف‌ها.",
     "مطالعهٔ مقدماتی ۳۰ تا ۵۰ نفره: آلفای کرونباخ، همبستگی گویه-کل (≥ ۰٫۳۰)، بررسی گویه‌های پرت و زمان تکمیل.",
     "مطالعهٔ اصلی: حداقل ۳۵۰ پرسشنامهٔ معتبر (ترجیحاً ۴۰۰ تا ۴۵۰)؛ تحلیل عاملی تأییدی، پایایی ترکیبی، AVE، HTMT، سوگیری روش مشترک (آزمون تک‌عاملی هارمن و مدل عامل روش مشترک).",
     "اخلاق: رضایت آگاهانه، بی‌نامی، حذف دادهٔ شناسایی‌کننده، و دریافت کد اخلاق از کمیتهٔ اخلاق دانشگاه پیش از توزیع."]
    for i, s in enumerate(steps, 1): d.para(f"**گام {fa(str(i))}.** " + s, indent=False)
    d.heading("۵. فرم پانل متخصصان (CVR و CVI)")
    d.para("برای هر گویه، «ضروری بودن» را با یکی از سه گزینه (ضروری / مفید اما غیرضروری / غیرضروری) و «ارتباط گویه با سازه» را با نمرهٔ ۱ (نامرتبط) تا ۴ (کاملاً مرتبط) مشخص کنید.", indent=False)
    rows = [[c, "☐ ☐ ☐", "۱ ۲ ۳ ۴", ""] for k in cons for c, _ in I.ITEMS[k]]
    d.table("جدول ۴. فرم ارزیابی متخصصان", ["کد گویه", "ضروری | مفید | غیرضروری", "ارتباط (۱ تا ۴)", "پیشنهاد اصلاح"], rows, widths=[1100, 2800, 1800, 3300], size=20)
    d.heading("۶. منابع (APA)")
    keys = sorted({x for k in cons for x in I.CONSTRUCTS[k][2]} | {"lawshe1975", "polit2006", "brislin1970", "fornell1981", "henseler2015", "hu1999", "podsakoff2003"})
    for k in sorted(keys, key=lambda k: LAT[k][0].lower()): d.reference(apa_latin(k), latin=True)
    d.save(os.path.join(D, f"paper{p}", f"Paper{p}_Questionnaire.docx"))
    return d.fn_count

# ------------------------------------------------------------------ چکیدهٔ گسترده
def ext_abstract(p):
    R = json.load(open(os.path.join(H, "..", f"paper{p}", "output", f"results_paper{p}.json"), encoding="utf-8"))
    d = Doc(body_pt=12); P = R["paths"]; I_ = R["indirect"]
    en = lambda x, nd=2: f"{x:.{nd}f}"
    def pe(k): v = P[k]; return f"β = {v['beta']:.2f}, z = {v['z']:.2f}, p {'< .001' if v['p'] < .001 else '= ' + format(v['p'], '.3f').lstrip('0')}"
    def pf(k): v = P[k]; return f"{S('β = ' + format(v['beta'], '.2f'))}، {S('z = ' + format(v['z'], '.2f'))}، " + (S("p < 0.001") if v["p"] < .001 else S("p = " + format(v["p"], ".3f")))
    ci_en = lambda v: f"[{v['lo']:.3f}, {v['hi']:.3f}]"; ci_fa = lambda v: f"[{num(v['lo'], 3)}، {num(v['hi'], 3)}]"
    if p == 1:
        cf, sm, sl = R["cfa"], R["sem"], R["simple_slopes"]
        fa_sec = [
         ("مقدمه و هدف", f"ریزش بورس تهران پس از رونق سال‌های ۱۳۹۹ و ۱۴۰۰ پرسشی جدی را مطرح کرد: آیا مواجهه مکرر سرمایه‌گذاران حقیقی با محتوای سرمایه‌گذاری در شبکه‌های اجتماعی تنها اطلاعات می‌افزاید یا از راه سازوکارهای هیجانی و اجتماعی کیفیت تصمیم را کاهش می‌دهد؟ هدف این پژوهش آزمون مسیر مواجهه با محتوا ← ترس از دست دادن فرصت (فومو) ← رفتار توده‌وار ← کیفیت تصمیم و بررسی نقش تعدیل‌گر استفاده از اطلاعات حسابداری در این مسیر است."),
         ("مبانی نظری و فرضیه‌ها", "چارچوب نظری بر نظریهٔ آبشارهای اطلاعاتی (بیکچندانی و همکاران، ۱۹۹۲)، نظریهٔ مقایسهٔ اجتماعی (فستینگر، ۱۹۵۴) و ادبیات فومو (پرزیبیلسکی و همکاران، ۲۰۱۳) استوار است. هشت فرضیه تدوین شد: اثر مثبت مواجهه بر فومو، اثر مثبت فومو بر رفتار توده‌وار، اثر منفی رفتار توده‌وار بر کیفیت تصمیم، اثر مستقیم مثبت مواجهه بر توده‌واری، میانجی‌گری متوالی، تعامل منفی فومو و اطلاعات حسابداری بر توده‌واری، میانجی‌گری تعدیل‌شده، و اثر مثبت اطلاعات حسابداری بر کیفیت تصمیم."),
         ("روش‌شناسی", f"پژوهش کمّی و پیمایشی با مدل‌سازی معادلات ساختاری مبتنی بر کوواریانس است. ابزار، پرسشنامه‌ای ۲۶ گویه‌ای لیکرت پنج‌درجه‌ای برای پنج سازه است. داده‌های {fa(str(R['n']))} سرمایه‌گذار حقیقی با شبیه‌سازی واقع‌نما (بارهای عاملی ۰٫۶۰ تا ۰٫۸۰، بارگذاری‌های متقاطع کوچک، همبستگی خطا و عامل روش ضعیف) تولید شد؛ بنابراین نتایج جنبهٔ نمایشی و روش‌شناختی دارند. تحلیل شامل CFA، پایایی و روایی، سوگیری روش مشترک، مدل ساختاری مکنون با تعامل مکنون (شاخص‌های حاصل‌ضرب جفت‌شده)، خودگردان‌سازی {fa(str(R['boot_n']))} تکراری و آزمون‌های استحکام (مدل‌های رقیب، DWLS، حذف دورترین مشاهدات) بود."),
         ("یافته‌ها", f"مدل اندازه‌گیری برازش مطلوب داشت ({S('CFI = ' + format(cf['cfi'], '.3f'))}؛ {S('RMSEA = ' + format(cf['rmsea'], '.3f'))}؛ {S('SRMR = ' + format(cf['srmr'], '.3f'))}) و پایایی و روایی پذیرفتنی بود. مواجهه فومو را افزایش داد ({pf('FOMO~SME')})، فومو رفتار توده‌وار را تقویت کرد ({pf('HRD~FOMO')}) و رفتار توده‌وار کیفیت تصمیم را کاهش داد ({pf('IDQ~HRD')}). اثر مستقیم مواجهه بر توده‌واری معنادار بود ({pf('HRD~SME')}). اثر غیرمستقیم متوالی استاندارد {num(I_['std_seq']['est'], 3)} با فاصلهٔ اطمینان {ci_fa(I_['std_seq'])} بود. تعامل فومو × اطلاعات حسابداری منفی و معنادار بود ({pf('HRD~INT')}): شیب فومو ← توده‌واری از {num(sl['low']['b'], 2)} در سطح پایین به {num(sl['high']['b'], 2)} در سطح بالای اطلاعات حسابداری کاهش یافت و شاخص میانجی‌گری تعدیل‌شده {num(I_['imm']['est'], 3)} {ci_fa(I_['imm'])} بود. اثر مستقیم فومو بر کیفیت تصمیم معنادار نبود."),
         ("بحث و نتیجه‌گیری", "در چارچوب مدل مفروض، همهٔ فرضیه‌ها تأیید شد. بخش عمده‌ای از اثر منفی مواجهه با محتوای شبکه‌ها بر کیفیت تصمیم از مسیر فومو و رفتار توده‌وار منتقل می‌شود و استفاده از اطلاعات حسابداری مانند سپری شناختی اثر فومو بر توده‌واری را تضعیف می‌کند، اما آن را حذف نمی‌کند. ترتیب علّی فومو و توده‌واری از نظر آماری قابل‌تفکیک نیست (مدل‌های هم‌ارز) و باید با طرح‌های طولی یا آزمایشی آزموده شود."),
         ("دانش‌افزایی و کاربرد", "پژوهش شبکه‌های اجتماعی، فومو و توده‌واری را در یک مدل متوالی پیوند می‌دهد و اطلاعات حسابداری را به‌عنوان تعدیل‌گر رفتاری معرفی می‌کند. پیشنهادهای کاربردی: افشای تعارض منافع در تحلیل‌های شبکه‌ای، انتشار خلاصه‌های قابل‌فهم گزارش‌های مالی در کانال‌های سرمایه‌گذاران خرد، ادغام شاخص‌های بنیادی در پلتفرم‌های معاملاتی و آموزش خواندن صورت‌های مالی."),
         ("محدودیت‌ها", "داده شبیه‌سازی‌شده است و نتایج شواهد تجربی دربارهٔ بازار واقعی نیستند؛ طرح مقطعی است؛ سازه‌ها خودگزارشی‌اند؛ و گویه‌ها پیش از کاربرد واقعی نیازمند اعتبارسنجی هستند."),
        ]
        en_sec = [
         ("Introduction and objective", "The Tehran Stock Exchange boom of 2020–2021 and the crash that followed raise a pressing question: does repeated exposure to investment content on social media merely add information for individual investors, or does it impair their decisions through emotional and social mechanisms? This study tests the pathway exposure to social-media investment content → fear of missing out (FOMO) → herding → investment decision quality, and examines whether the use of accounting information moderates this pathway."),
         ("Theoretical background and hypotheses", "The framework draws on information-cascade theory (Bikhchandani, Hirshleifer, & Welch, 1992), social-comparison theory (Festinger, 1954), and the FOMO literature (Przybylski et al., 2013). Eight hypotheses were derived: positive effects of exposure on FOMO and of FOMO on herding; a negative effect of herding on decision quality; a direct positive effect of exposure on herding; sequential mediation; a negative FOMO × accounting-information-use interaction on herding; moderated mediation; and a positive effect of accounting information use on decision quality."),
         ("Methodology", f"The study is quantitative and survey-based, using covariance-based structural equation modeling. The instrument is a 26-item, five-point Likert questionnaire covering five constructs. Data for {R['n']} individual investors were generated by a realistic simulation (loadings .60–.80, small cross-loadings, correlated residuals, and a weak common-method factor); the results are therefore illustrative and methodological. Analyses comprised confirmatory factor analysis, reliability and validity assessment, common-method-bias checks, a latent structural model with a latent interaction (matched-pair product indicators), {R['boot_n']} bootstrap resamples, and robustness checks (competing models, DWLS estimation, trimming the 5% most distant observations)."),
         ("Findings", f"The measurement model fit well (CFI = {en(cf['cfi'],3)}, RMSEA = {en(cf['rmsea'],3)}, SRMR = {en(cf['srmr'],3)}) with acceptable reliability and validity. Exposure increased FOMO ({pe('FOMO~SME')}), FOMO strengthened herding ({pe('HRD~FOMO')}), and herding reduced decision quality ({pe('IDQ~HRD')}). Exposure also had a direct effect on herding ({pe('HRD~SME')}). The standardized sequential indirect effect was {en(I_['std_seq']['est'],3)} (95% bootstrap CI {ci_en(I_['std_seq'])}). The FOMO × accounting-information-use interaction was negative and significant ({pe('HRD~INT')}): the slope of herding on FOMO fell from {en(sl['low']['b'])} at low to {en(sl['high']['b'])} at high accounting information use, and the index of moderated mediation was {en(I_['imm']['est'],3)} {ci_en(I_['imm'])}. The direct effect of FOMO on decision quality was not significant."),
         ("Discussion and conclusion", "Within the assumed data-generating model, all hypotheses were supported. Much of the harmful effect of social-media exposure on decision quality is transmitted through FOMO and herding, and accounting information use acts as a cognitive buffer that weakens, but does not eliminate, the effect of FOMO on herding. The causal order of FOMO and herding cannot be distinguished statistically (equivalent models) and needs longitudinal or experimental testing."),
         ("Contribution and implications", "The study links social media, FOMO, and herding in a single sequential model and introduces accounting information use as a behavioral moderator. Practical implications include disclosure of conflicts of interest in online analyses, plain-language summaries of financial statements in the channels used by retail investors, fundamentals embedded in trading platforms, and education in reading financial statements."),
         ("Limitations", "The data are simulated, so the results are not empirical evidence about the real market; the design is cross-sectional; constructs are self-reported; and the items require validation before real-data use."),
        ]
        kw_fa = "مواجهه با شبکه‌های اجتماعی؛ فومو؛ رفتار توده‌وار؛ اطلاعات حسابداری؛ کیفیت تصمیم سرمایه‌گذاری؛ مدل‌سازی معادلات ساختاری؛ بورس تهران"
        kw_en = "Social media exposure; FOMO; Herding; Accounting information; Investment decision quality; Structural equation modeling; Tehran Stock Exchange"
    else:
        cf, sm, inv, gp, ml, mt, sh, G = R["cfa"], R["sem"], R["invariance"], R["group_paths"], R["ml"], R["ml_tests"], R["shap"], R["groups"]
        top = list(sh["importance"])[:2]
        NMF = {"FOMO": "فومو", "AIU": "استفاده از اطلاعات حسابداری"}; NME = {"FOMO": "FOMO", "AIU": "accounting information use"}
        fa_sec = [
         ("مقدمه و هدف", "سرمایه‌گذار حقیقی میان جریان پرشتاب و هیجانی شبکه‌های اجتماعی و جریان کندتر اما قابل‌راستی‌آزمایی گزارش‌های مالی دچار رقابت توجه است. هدف این پژوهش بررسی پیش‌برنده‌های ترس از دست دادن فرصت (فومو)، رقابت میان محتوای شبکه‌ها و اطلاعات حسابداری، تفاوت ساختار و مسیرها میان سرمایه‌گذاران دارای و فاقد تجربهٔ زیان در ریزش بورس، و ارزیابی تکمیلی مدل‌های غیرخطی یادگیری ماشین است."),
         ("مبانی نظری و فرضیه‌ها", "نظریهٔ مقایسهٔ اجتماعی (فستینگر، ۱۹۵۴)، نظریهٔ پشیمانی (لومز و ساگدن، ۱۹۸۲؛ بل، ۱۹۸۲) و توجه محدود (باربر و اودین، ۲۰۰۸) مبنای دوازده فرضیه‌اند: اثر مثبت مقایسهٔ اجتماعی و پشیمانی پیش‌بینی‌شده بر فومو، اثر منفی مواجهه با محتوا بر استفاده از اطلاعات حسابداری (جایگزینی)، اثر مثبت سواد حسابداری بر استفاده از آن، اثر منفی فومو و اثر مثبت اطلاعات حسابداری بر کیفیت تصمیم، اثرهای غیرمستقیم، ناوردایی اندازه‌گیری، قوی‌تر بودن اثر پشیمانی بر فومو و اثر منفی فومو بر کیفیت تصمیم در گروه دارای تجربهٔ زیان، برتری پیش‌بینی مدل‌های غیرخطی و هم‌خوانی اهمیت SHAP با مدل ساختاری."),
         ("روش‌شناسی", f"پرسشنامهٔ ۳۳ گویه‌ای لیکرت پنج‌درجه‌ای برای هفت سازه به‌کار رفت. داده‌های {fa(str(R['n']))} سرمایه‌گذار حقیقی ({fa(str(G['n1']))} نفر دارای تجربهٔ زیان) به‌صورت شبیه‌سازی واقع‌نما و مستقل از مقالهٔ همراه تولید شد؛ نتایج نمایشی و روش‌شناختی‌اند. تحلیل شامل مدل ساختاری مکنون با {fa(str(R['boot_n']))} تکرار خودگردان، CFA چندگروهی (پیکربندی، متریک، اسکالر)، مقایسهٔ مسیرها با آزمون z و خودگردان‌سازی، و مقایسهٔ رگرسیون خطی با جنگل تصادفی و تقویت گرادیان (اعتبارسنجی متقاطع ۵ لایه‌ای × ۱۰ تکرار، آزمون t اصلاح‌شده) و تفسیر SHAP بود."),
         ("یافته‌ها", f"برازش مدل اندازه‌گیری مطلوب بود ({S('CFI = ' + format(cf['cfi'], '.3f'))}؛ {S('RMSEA = ' + format(cf['rmsea'], '.3f'))}). مقایسهٔ اجتماعی ({pf('FOMO~SC')}) و پشیمانی پیش‌بینی‌شده ({pf('FOMO~AR')}) فومو را افزایش دادند؛ مواجهه، استفاده از اطلاعات حسابداری را کاهش داد ({pf('AIU~SME')}) و سواد حسابداری آن را افزایش داد ({pf('AIU~AL')}). فومو کیفیت تصمیم را کاهش ({pf('IDQ~FOMO')}) و استفاده از اطلاعات حسابداری آن را افزایش داد ({pf('IDQ~AIU')}). ناوردایی اسکالر برقرار بود ({S('ΔCFI = ' + format(inv['scalar']['cfi'] - inv['metric']['cfi'], '.3f'))}). اثر پشیمانی بر فومو ({S('Δb = ' + format(gp['FOMO~AR']['diff'], '.2f'))}) و اثر فومو بر کیفیت تصمیم ({S('Δb = ' + format(gp['IDQ~FOMO']['diff'], '.2f'))}) در گروه دارای تجربهٔ زیان قوی‌تر بود. R² بیرون‌نمونه‌ای رگرسیون خطی {F3(ml['OLS']['r2']['m'])}، جنگل تصادفی {F3(ml['RF']['r2']['m'])} و تقویت گرادیان {F3(ml['GBM']['r2']['m'])} بود؛ مهم‌ترین پیش‌بینی‌کننده‌های SHAP {NMF[top[0]]} و {NMF[top[1]]} بودند."),
         ("بحث و نتیجه‌گیری", "فومو را مقایسهٔ اجتماعی و پشیمانی پیش‌بینی‌شده تغذیه می‌کنند و فومو و اطلاعات حسابداری در دو سوی ترازوی کیفیت تصمیم قرار دارند. مواجهه با محتوای شبکه‌ها هم از راه افزایش فومو و هم از راه جایگزینی اطلاعاتی به تصمیم آسیب می‌زند. تجربهٔ زیان حساسیت به پشیمانی و پیامد فومو را تقویت می‌کند، اما اثر مفید اطلاعات حسابداری در دو گروه مشابه است."),
         ("دانش‌افزایی و کاربرد", "ترکیب مدل‌سازی معادلات ساختاری و یادگیری ماشین تفسیرپذیر، آزمون نظریه و کشف اثرهای غیرخطی را هم‌زمان ممکن می‌کند. کاربردها: غربال‌گری رفتاری سرمایه‌گذاران زیان‌دیده، هشدارهای «فرصت از دست‌رفته» همراه با شاخص‌های بنیادی و آموزش تبدیل سواد حسابداری به رفتار استفاده از اطلاعات."),
         ("محدودیت‌ها", "داده شبیه‌سازی‌شده است؛ مقایسهٔ مسیرها با مدل‌های جداگانه انجام شد؛ ابرپارامترهای یادگیری ماشین از پیش ثابت شدند؛ آزمون هم‌خوانی SHAP با مدل ساختاری تنها بر شش سازه استوار است؛ و گویه‌ها پیش از کاربرد واقعی نیازمند اعتبارسنجی‌اند."),
        ]
        en_sec = [
         ("Introduction and objective", "Individual investors face a competition for attention between the fast, emotional stream of social media and the slower but verifiable stream of financial reports. This study examines the antecedents of fear of missing out (FOMO), the competition between social-media content and accounting information, differences in structure and paths between investors with and without losses in the stock-market crash, and, as a complement, nonlinear machine-learning models."),
         ("Theoretical background and hypotheses", "Social-comparison theory (Festinger, 1954), regret theory (Loomes & Sugden, 1982; Bell, 1982), and limited attention (Barber & Odean, 2008) underpin twelve hypotheses: positive effects of social comparison and anticipated regret on FOMO; a negative effect of content exposure on accounting information use (substitution); a positive effect of accounting literacy on its use; a negative effect of FOMO and a positive effect of accounting information use on decision quality; indirect effects; measurement invariance; a stronger regret → FOMO effect and a more negative FOMO → decision quality effect among investors with losses; superior out-of-sample prediction by nonlinear models; and agreement between SHAP importance and the structural model."),
         ("Methodology", f"A 33-item, five-point Likert questionnaire measured seven constructs. Data for {R['n']} individual investors ({G['n1']} with loss experience) were generated by a realistic simulation independent of the companion article; results are illustrative and methodological. Analyses included a latent structural model with {R['boot_n']} bootstrap resamples, multi-group CFA (configural, metric, scalar invariance), path comparison with z tests and bootstrap intervals, and a comparison of linear regression with random forest and gradient boosting (5-fold × 10 repeated cross-validation, corrected resampled t test) with SHAP interpretation."),
         ("Findings", f"The measurement model fit well (CFI = {en(cf['cfi'],3)}, RMSEA = {en(cf['rmsea'],3)}). Social comparison ({pe('FOMO~SC')}) and anticipated regret ({pe('FOMO~AR')}) increased FOMO; exposure decreased accounting information use ({pe('AIU~SME')}) and accounting literacy increased it ({pe('AIU~AL')}). FOMO reduced decision quality ({pe('IDQ~FOMO')}), while accounting information use improved it ({pe('IDQ~AIU')}). Scalar invariance held (ΔCFI = {en(inv['scalar']['cfi'] - inv['metric']['cfi'],3)}). The effect of regret on FOMO (Δb = {en(gp['FOMO~AR']['diff'])}) and of FOMO on decision quality (Δb = {en(gp['IDQ~FOMO']['diff'])}) were stronger among investors with losses. Out-of-sample R² was {en(ml['OLS']['r2']['m'],3)} for linear regression, {en(ml['RF']['r2']['m'],3)} for random forest, and {en(ml['GBM']['r2']['m'],3)} for gradient boosting; the two most important SHAP predictors were {NME[top[0]]} and {NME[top[1]]}."),
         ("Discussion and conclusion", "FOMO is fed by social comparison and anticipated regret, and FOMO and accounting information use sit on opposite sides of decision quality. Content exposure harms decisions both by raising FOMO and by displacing accounting information. Loss experience amplifies sensitivity to regret and to the consequences of FOMO, whereas the benefit of accounting information is similar in both groups."),
         ("Contribution and implications", "Combining structural equation modeling with interpretable machine learning allows theory testing and the detection of nonlinear effects at the same time. Implications include behavioral screening of investors who suffered losses, 'missed-opportunity' alerts paired with fundamental indicators, and training that turns accounting literacy into actual information use."),
         ("Limitations", "The data are simulated; path comparisons used separate-group models; machine-learning hyperparameters were fixed in advance; the SHAP–SEM agreement test rests on only six constructs; and the items require validation before real-data use."),
        ]
        kw_fa = "فومو؛ مقایسهٔ اجتماعی؛ پشیمانی پیش‌بینی‌شده؛ اطلاعات حسابداری؛ ناوردایی اندازه‌گیری؛ یادگیری ماشین؛ SHAP"
        kw_en = "FOMO; Social comparison; Anticipated regret; Accounting information; Measurement invariance; Machine learning; SHAP"
    d.title(TITLES[p][0]); d.para("**چکیدهٔ گسترده**", jc="center", indent=False, size=26, after=100)
    d.para("اعلان شفافیت: داده‌های این پژوهش شبیه‌سازی‌شده‌اند و نتایج جنبهٔ نمایشی و روش‌شناختی دارند.", indent=False, after=100, italic=True)
    for h, t in fa_sec: d.heading(h, 2); d.para(t, indent=False)
    d.para("**کلیدواژه‌ها:** " + kw_fa, indent=False, before=100)
    d.page_break()
    d.para(TITLES[p][1], jc="center", indent=False, rtl=False, persian=False, size=26, bold=True, font=d.lat, after=120)
    d.para("Extended Abstract", jc="center", indent=False, rtl=False, persian=False, size=24, bold=True, font=d.lat, after=60)
    d.para("Transparency note: the data in this study are simulated; the results are illustrative and methodological.", jc="left", indent=False, rtl=False, persian=False, size=24, font=d.lat, italic=True, after=100)
    for h, t in en_sec:
        d.para(h, jc="left", indent=False, rtl=False, persian=False, size=24, bold=True, font=d.lat, before=100, after=40)
        d.para(t, jc="both", indent=False, rtl=False, persian=False, size=24, font=d.lat, after=60)
    d.para("Keywords: " + kw_en, jc="left", indent=False, rtl=False, persian=False, size=24, font=d.lat, before=100)
    d.save(os.path.join(D, f"paper{p}", f"Paper{p}_Extended_Abstract_FA_EN.docx"))

# ------------------------------------------------------------------ فرم‌های ارسال
def forms(p):
    d = Doc(body_pt=12); other = 2 if p == 1 else 1
    d.title("بستهٔ ارسال مقاله: نامهٔ سردبیر، اظهارنامه‌ها و چک‌لیست")
    d.heading("۱. نامهٔ ارسال به سردبیر")
    d.para("جناب آقای/سرکار خانم " + ph("نام سردبیر") + "، سردبیر محترم نشریهٔ علمی «کاوش‌های نوین در علوم محاسباتی و مدیریت رفتاری»", indent=False)
    d.para(f"با سلام و احترام؛ ضمن تقدیم احترام، مقالهٔ «{TITLES[p][0]}» را برای بررسی و چاپ در آن نشریهٔ ارجمند ارسال می‌کنم. این مقاله با رویکرد حسابداری رفتاری و روش مدل‌سازی معادلات ساختاری، " + ("سازوکار متوالی میان مواجهه با محتوای شبکه‌های اجتماعی، فومو، رفتار توده‌وار و کیفیت تصمیم را با تعدیل‌گری اطلاعات حسابداری بررسی می‌کند." if p == 1 else "پیش‌برنده‌های فومو، رقابت منابع اطلاعاتی و تفاوت مسیرها میان سرمایه‌گذاران دارای و فاقد تجربهٔ زیان را بررسی می‌کند و مدل ساختاری را با یادگیری ماشین تفسیرپذیر تکمیل می‌کند.") + " ")
    d.para(f"**ارتباط با مقالهٔ دیگر:** این مقاله و مقالهٔ همراه آن (مقالهٔ {'دوم' if p == 1 else 'اول'}) از یک طرح پژوهشی و یک ابزار واحد برآمده‌اند ولی پرسش پژوهش، مدل و سهم علمی متفاوت دارند و داده‌های تحلیل‌شدهٔ آن‌ها یکسان نیست. نشانی مقالهٔ همراه: " + ph("عنوان و وضعیت مقالهٔ همراه") + ".", indent=False)
    d.para("**شفافیت دادهٔ پژوهش:** داده‌های نسخهٔ حاضر با شبیه‌سازی واقع‌نما تولید شده‌اند و پاسخ‌دهندهٔ واقعی ندارند؛ این موضوع در متن مقاله (بخش روش‌شناسی و محدودیت‌ها) به‌صراحت اعلام شده است. " + ph("اگر پیش از ارسال داده‌ٔ واقعی جایگزین شد، این بند را حذف و شرح گردآوری داده را جایگزین کنید.") , indent=False)
    d.para("تأیید می‌کنم مقاله پیش‌تر منتشر نشده و هم‌زمان برای نشریهٔ دیگری ارسال نشده است. با احترام، " + ph("نام و امضای نویسندهٔ مسئول، تاریخ"), indent=False)
    d.heading("۲. اظهارنامه‌ها")
    rows = [["اصالت و عدم ارسال هم‌زمان", "اثر حاضر اصیل است، پیش‌تر منتشر نشده و در نشریهٔ دیگری در دست بررسی نیست."],
            ["تعارض منافع", ph("نویسندگان اعلام می‌کنند تعارض منافعی ندارند / شرح دهید.")],
            ["منابع مالی", ph("حامی مالی را بنویسید یا «این پژوهش حمایت مالی نداشته است».")],
            ["ملاحظات اخلاقی", "نسخهٔ حاضر شامل دادهٔ انسانی واقعی نیست (داده شبیه‌سازی‌شده). در اجرای واقعی: رضایت آگاهانه، بی‌نامی پاسخ‌ها و دریافت کد اخلاق ضروری است. " + ph("کد اخلاق (در صورت وجود)")],
            ["دسترسی به داده و کد", "داده، پرسشنامه، کد پایتون و دفترچهٔ Colab در پیوست ارائه شده‌اند و نتایج با بذر ثابت بازتولیدپذیرند."],
            ["استفاده از ابزارهای هوش مصنوعی و نرم‌افزار", "تحلیل با پایتون (semopy، statsmodels، scikit-learn، shap) انجام شده است. " + ph("بر پایهٔ سیاست نشریه، میزان کمک ابزارهای هوش مصنوعی در نگارش و کدنویسی را اعلام کنید.")]]
    d.table("جدول ۱. اظهارنامه‌ها", ["عنوان", "متن"], rows, widths=[2600, 6400], size=22)
    d.heading("۳. سهم نویسندگان (CRediT)")
    roles = ["مفهوم‌سازی", "روش‌شناسی", "نرم‌افزار و کدنویسی", "اعتبارسنجی", "تحلیل رسمی", "گردآوری داده", "نگارش پیش‌نویس", "ویرایش و بازبینی", "نظارت"]
    d.table("جدول ۲. نقش نویسندگان", ["نقش", "نویسنده اول", "نویسنده دوم"], [[r, "☐", "☐"] for r in roles], widths=[4000, 2500, 2500], size=22)
    d.heading("۴. چک‌لیست انطباق با راهنمای نویسندگان نشریه")
    chk = [("فایل Word (docx)، کاغذ A4، حاشیه ۲٫۵ سانتی‌متر، فاصلهٔ خطوط ساده", "انجام شد" if p == 1 else "قالب آزاد (نشریه برای مقالهٔ ۲ الزام نداشت)"),
           ("صفحهٔ عنوان: عنوان، نویسندگان، وابستگی، ایمیل نویسندهٔ مسئول با ستاره", "انجام شد؛ اطلاعات واقعی را جایگزین کنید" if p == 1 else "—"),
           ("چکیده ۱۵۰ تا ۳۰۰ کلمه با هدف، روش، یافته‌ها، نتیجه‌گیری و دانش‌افزایی؛ ۴ تا ۷ کلیدواژه", "انجام شد (۲۳۴ کلمه، ۷ کلیدواژه)" if p == 1 else "—"),
           ("بخش‌ها: مقدمه، مبانی نظری (بدون تیتر جداگانهٔ پیشینه)، روش‌شناسی، یافته‌ها، بحث و نتیجه‌گیری", "انجام شد" if p == 1 else "انجام شد (ساختار مشابه)"),
           ("ارجاع APA با نام فارسی نویسنده و اصل لاتین در پاورقی؛ همهٔ اعداد فارسی", "انجام شد" if p == 1 else "—"),
           ("DOI تمام مقالات در فهرست منابع", "منابع لاتین دارند؛ **صحت DOI را با Crossref بررسی کنید**"),
           ("منابع فارسی ثبت‌شده با DOI", "نیازمند اقدام نویسنده (یک منبع تأییدشده؛ بقیه را اضافه کنید)"),
           ("فونت‌ها: عنوان B Zar 12 Bold؛ تیتر و چکیده B Nazanin؛ متن B Nazanin 13؛ پاورقی Times 11", "اعمال شد؛ فونت‌ها باید در Word نصب باشند" if p == 1 else "—"),
           ("جدول‌ها (شماره و عنوان بالا) و شکل‌ها (شماره و عنوان پایین) با اعداد فارسی", "انجام شد" if p == 1 else "—"),
           ("اعتبارسنجی پرسشنامه (CVR/CVI و مطالعهٔ مقدماتی) و جایگزینی دادهٔ واقعی", "نیازمند اقدام نویسنده")]
    d.table("جدول ۳. چک‌لیست", ["مورد", "وضعیت"], [[a, b] for a, b in chk], widths=[5600, 3400], size=22)
    d.save(os.path.join(D, f"paper{p}", f"Paper{p}_Submission_Forms.docx"))
for p in (1, 2):
    questionnaire(p); ext_abstract(p); forms(p)
print("docs ok")
