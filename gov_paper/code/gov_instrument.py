# -*- coding: utf-8 -*-
"""Instrument for the public-sector paper: items (Persian), origin class, references per scale; reference list (APA) and citation map."""
RB = "پژوهش‌محور (اقتباس‌شده)"; RM = "محقق‌ساخته (برگرفته از نظریه)"; MIX = "ترکیبی (بخشی اقتباس‌شده، بخشی محقق‌ساخته)"
LIK = "لیکرت ۵‌درجه‌ای: ۱ = کاملاً مخالف … ۵ = کاملاً موافق"
LAT = {
"dimaggio1983": "DiMaggio, P. J., & Powell, W. W. (1983). The iron cage revisited: Institutional isomorphism and collective rationality in organizational fields. //American Sociological Review, 48//(2), 147–160. https://doi.org/10.2307/2095101",
"meyer1977": "Meyer, J. W., & Rowan, B. (1977). Institutionalized organizations: Formal structure as myth and ceremony. //American Journal of Sociology, 83//(2), 340–363. https://doi.org/10.1086/226550",
"scott2014": "Scott, W. R. (2014). //Institutions and organizations: Ideas, interests, and identities// (4th ed.). Thousand Oaks, CA: Sage.",
"oliver1991": "Oliver, C. (1991). Strategic responses to institutional processes. //Academy of Management Review, 16//(1), 145–179. https://doi.org/10.5465/amr.1991.4279002",
"bromley2012": "Bromley, P., & Powell, W. W. (2012). From smoke and mirrors to walking the talk: Decoupling in the contemporary world. //Academy of Management Annals, 6//(1), 483–530. https://doi.org/10.5465/19416520.2012.684462",
"brignall2000": "Brignall, S., & Modell, S. (2000). An institutional perspective on performance measurement and management in the “new public sector”. //Management Accounting Research, 11//(3), 281–306. https://doi.org/10.1006/mare.2000.0136",
"modell2009": "Modell, S. (2009). Institutional research on performance measurement and management in the public sector accounting literature: A review and assessment. //Financial Accountability & Management, 25//(3), 277–303. https://doi.org/10.1111/j.1468-0408.2009.00478.x",
"teo2003": "Teo, H. H., Wei, K. K., & Benbasat, I. (2003). Predicting intention to adopt interorganizational linkages: An institutional perspective. //MIS Quarterly, 27//(1), 19–49. https://doi.org/10.2307/30036518",
"bovens2007": "Bovens, M. (2007). Analysing and assessing accountability: A conceptual framework. //European Law Journal, 13//(4), 447–468. https://doi.org/10.1111/j.1468-0386.2007.00378.x",
"bracci2015": "Bracci, E., Humphrey, C., Moll, J., & Steccolini, I. (2015). Public sector accounting, accountability and austerity: More than balancing the books? //Accounting, Auditing & Accountability Journal, 28//(6), 878–908. https://doi.org/10.1108/AAAJ-06-2015-2089",
"lapsley2009": "Lapsley, I. (2009). New public management: The cruellest invention of the human spirit? //Abacus, 45//(1), 1–21. https://doi.org/10.1111/j.1467-6281.2009.00275.x",
"hood1991": "Hood, C. (1991). A public management for all seasons? //Public Administration, 69//(1), 3–19. https://doi.org/10.1111/j.1467-9299.1991.tb00779.x",
"pollitt2017": "Pollitt, C., & Bouckaert, G. (2017). //Public management reform: A comparative analysis – into the age of austerity// (4th ed.). Oxford, UK: Oxford University Press.",
"moynihan2008": "Moynihan, D. P. (2008). //The dynamics of performance management: Constructing information and reform//. Washington, DC: Georgetown University Press.",
"moynihan2010": "Moynihan, D. P., & Pandey, S. K. (2010). The big question for performance management: Why do managers use performance information? //Journal of Public Administration Research and Theory, 20//(4), 849–866. https://doi.org/10.1093/jopart/muq004",
"kroll2015": "Kroll, A. (2015). Drivers of performance information use: Systematic literature review and directions for future research. //Public Performance & Management Review, 38//(3), 459–486. https://doi.org/10.1080/15309576.2015.1006469",
"pina2009": "Pina, V., Torres, L., & Yetano, A. (2009). Accrual accounting in EU local governments: One method, several approaches. //European Accounting Review, 18//(4), 765–807. https://doi.org/10.1080/09638180902863792",
"christiaens2010": "Christiaens, J., Reyniers, B., & Rollé, C. (2010). Impact of IPSAS on reforming governmental financial information systems: A comparative study. //International Review of Administrative Sciences, 76//(3), 537–554. https://doi.org/10.1177/0020852310372450",
"christiaens2015": "Christiaens, J., Vanhee, C., Manes-Rossi, F., Aversano, N., & Van Cauwenberge, P. (2015). The effect of IPSAS on reforming governmental financial reporting: An international comparison. //International Review of Administrative Sciences, 81//(1), 158–177. https://doi.org/10.1177/0020852314546580",
"dunleavy2006": "Dunleavy, P., Margetts, H., Bastow, S., & Tinkler, J. (2006). New public management is dead—long live digital-era governance. //Journal of Public Administration Research and Theory, 16//(3), 467–494. https://doi.org/10.1093/jopart/mui057",
"delone2003": "DeLone, W. H., & McLean, E. R. (2003). The DeLone and McLean model of information systems success: A ten-year update. //Journal of Management Information Systems, 19//(4), 9–30. https://doi.org/10.1080/07421222.2003.11045748",
"moore1995": "Moore, M. H. (1995). //Creating public value: Strategic management in government//. Cambridge, MA: Harvard University Press.",
"fornell1981": "Fornell, C., & Larcker, D. F. (1981). Evaluating structural equation models with unobservable variables and measurement error. //Journal of Marketing Research, 18//(1), 39–50. https://doi.org/10.1177/002224378101800104",
"hu1999": "Hu, L., & Bentler, P. M. (1999). Cutoff criteria for fit indexes in covariance structure analysis: Conventional criteria versus new alternatives. //Structural Equation Modeling, 6//(1), 1–55. https://doi.org/10.1080/10705519909540118",
"henseler2015": "Henseler, J., Ringle, C. M., & Sarstedt, M. (2015). A new criterion for assessing discriminant validity in variance-based structural equation modeling. //Journal of the Academy of Marketing Science, 43//(1), 115–135. https://doi.org/10.1007/s11747-014-0403-8",
"marsh2004": "Marsh, H. W., Wen, Z., & Hau, K.-T. (2004). Structural equation models of latent interactions: Evaluation of alternative estimation strategies and indicator construction. //Psychological Methods, 9//(3), 275–300. https://doi.org/10.1037/1082-989X.9.3.275",
"little2006": "Little, T. D., Bovaird, J. A., & Widaman, K. F. (2006). On the merits of orthogonalizing powered and product terms: Implications for modeling interactions among latent variables. //Structural Equation Modeling, 13//(4), 497–519. https://doi.org/10.1207/s15328007sem1304_1",
"preacher2008": "Preacher, K. J., & Hayes, A. F. (2008). Asymptotic and resampling strategies for assessing and comparing indirect effects in multiple mediator models. //Behavior Research Methods, 40//(3), 879–891. https://doi.org/10.3758/BRM.40.3.879",
"hayes2015": "Hayes, A. F. (2015). An index and test of linear moderated mediation. //Multivariate Behavioral Research, 50//(1), 1–22. https://doi.org/10.1080/00273171.2014.962683",
"maccallum1996": "MacCallum, R. C., Browne, M. W., & Sugawara, H. M. (1996). Power analysis and determination of sample size for covariance structure modeling. //Psychological Methods, 1//(2), 130–149. https://doi.org/10.1037/1082-989X.1.2.130",
"igolkina2020": "Igolkina, A. A., & Meshcheryakov, G. (2020). semopy: A Python package for structural equation modeling. //Structural Equation Modeling, 27//(6), 952–963. https://doi.org/10.1080/10705511.2019.1704289",
"podsakoff2003": "Podsakoff, P. M., MacKenzie, S. B., Lee, J.-Y., & Podsakoff, N. P. (2003). Common method biases in behavioral research: A critical review of the literature and recommended remedies. //Journal of Applied Psychology, 88//(5), 879–903. https://doi.org/10.1037/0021-9010.88.5.879",
"lawshe1975": "Lawshe, C. H. (1975). A quantitative approach to content validity. //Personnel Psychology, 28//(4), 563–575. https://doi.org/10.1111/j.1744-6570.1975.tb01393.x",
"polit2006": "Polit, D. F., & Beck, C. T. (2006). The content validity index: Are you sure you know what's being reported? Critique and recommendations. //Research in Nursing & Health, 29//(5), 489–497. https://doi.org/10.1002/nur.20147",
}
# Persian references (details from journal pages; names/years/pages to be verified against the printed article)
FAR = {
"pourghaffar": dict(fa="پورغفار، جواد؛ محمدزاده سالطه، حیدر؛ زینالی، مهدی و مهرانی، ساسان (۱۴۰۱). الگوی بودجه‌ریزی بر مبنای عملکرد با رویکرد گزارشگری مالی بهنگام در بخش عمومی ایران. //حسابداری دولتی، ۸//(۲)، ۲۱-۳۶.",
   en="Pourghaffar, J., Mohammadzadeh Salteh, H., Zeinali, M., & Mehrani, S. (2022). Performance-based budgeting model with a real time financial reporting approach in Iran public sector. //Governmental Accounting, 8//(2), 21–36. https://doi.org/10.30473/gaa.2022.61861.1528 (in Persian)", cite=("پورغفار و همکاران", "Pourghaffar et al.", 1401)),
"ahmadi": dict(fa="احمدی، غلامرضا؛ ناظمی، امین و نمازی، نویدرضا (۱۴۰۲). شناسایی سازه‌های اثرگذار بر میزان اجرای بودجه‌ریزی مبتنی بر عملکرد با تأکید بر نظریهٔ شبکهٔ کنشگران. //پیشرفت‌های حسابداری، ۱۴//(۲)، ۱-۳۷.",
   en="Ahmadi, G., Nazemi, A., & Namazi, N. R. (2023). Identification of structures that affect performance-based budgeting with emphasis on actor network theory. //Journal of Accounting Advances, 14//(2), 1–37. https://doi.org/10.22099/JAA.2023.45244.2286 (in Persian)", cite=("احمدی، ناظمی و نمازی", "Ahmadi, Nazemi, & Namazi", 1402)),
"nourani": dict(fa="نورانی، حسین و اخلاقی یزدی‌نژاد، اسماعیل (۱۴۰۲). ارائهٔ الگوی رفع چالش‌ها و تنگناهای استانداردهای حسابداری بخش عمومی با استفاده از نظریهٔ داده‌بنیاد. //حسابداری دولتی، ۹//(۱۸)، ۱۵۱-۱۶۸.",
   en="Nourani, H., & Akhlaghi Yazdinejad, E. (2023). Presenting a model for solving the challenges and bottlenecks of public sector accounting standards using grounded theory. //Governmental Accounting, 9//(18), 151–168. (in Persian)", cite=("نورانی و اخلاقی یزدی‌نژاد", "Nourani & Akhlaghi Yazdinejad", 1402)),
"naroui": dict(fa="ناروئی، عبدالرحمان؛ مؤمنی، علیرضا و گرد، عزیز (۱۳۹۹). تدوین و ارزیابی مدل مطلوب نظام حسابداری تعهدی در بخش عمومی (مطالعهٔ موردی: مدیران و ذی‌حسابان دستگاه‌های اجرایی). //حسابداری دولتی، ۶//(۲)، ۴۷-۶۰.",
   en="Naroui, A., Momeni, A., & Gerd, A. (2020). Developing and evaluating an optimal model of the accrual accounting system in the public sector (case study: Managers and comptrollers of executive agencies). //Governmental Accounting, 6//(2), 47–60. https://doi.org/10.30473/gaa.2020.54322.1403 (in Persian)", cite=("ناروئی، مؤمنی و گرد", "Naroui, Momeni, & Gerd", 1399)),
}
CITE = {
"dimaggio1983": ("دی‌ماجیو و پاول", "DiMaggio & Powell", 1983), "meyer1977": ("مایر و روان", "Meyer & Rowan", 1977), "scott2014": ("اسکات", "Scott", 2014),
"oliver1991": ("الیور", "Oliver", 1991), "bromley2012": ("برومیلی و پاول", "Bromley & Powell", 2012), "brignall2000": ("بریگنال و مودل", "Brignall & Modell", 2000),
"modell2009": ("مودل", "Modell", 2009), "teo2003": ("تئو، وی و بنباسات", "Teo, Wei, & Benbasat", 2003), "bovens2007": ("بوونس", "Bovens", 2007),
"bracci2015": ("براچی، همفری، مول و استچولینی", "Bracci, Humphrey, Moll, & Steccolini", 2015), "lapsley2009": ("لپسلی", "Lapsley", 2009), "hood1991": ("هود", "Hood", 1991),
"pollitt2017": ("پولیت و بوکارت", "Pollitt & Bouckaert", 2017), "moynihan2008": ("موینیهان", "Moynihan", 2008), "moynihan2010": ("موینیهان و پاندی", "Moynihan & Pandey", 2010),
"kroll2015": ("کرول", "Kroll", 2015), "pina2009": ("پینا، تورس و یتانو", "Pina, Torres, & Yetano", 2009), "christiaens2010": ("کریستین‌س، رینرز و رول", "Christiaens, Reyniers, & Rollé", 2010),
"christiaens2015": ("کریستین‌س و همکاران", "Christiaens et al.", 2015), "dunleavy2006": ("دان‌لیوی و همکاران", "Dunleavy et al.", 2006), "delone2003": ("دلون و مک‌لین", "DeLone & McLean", 2003),
"moore1995": ("مور", "Moore", 1995), "fornell1981": ("فورنل و لارکر", "Fornell & Larcker", 1981), "hu1999": ("هو و بنتلر", "Hu & Bentler", 1999),
"henseler2015": ("هنسلر، رینگل و سارستدت", "Henseler, Ringle, & Sarstedt", 2015), "marsh2004": ("مارش، ون و هائو", "Marsh, Wen, & Hau", 2004), "little2006": ("لیتل، بووایرد و ویدمن", "Little, Bovaird, & Widaman", 2006),
"preacher2008": ("پریچر و هیز", "Preacher & Hayes", 2008), "hayes2015": ("هیز", "Hayes", 2015), "maccallum1996": ("مک‌کالوم، براون و سوگاوارا", "MacCallum, Browne, & Sugawara", 1996),
"igolkina2020": ("ایگولکینا و مشچریاکوف", "Igolkina & Meshcheryakov", 2020), "podsakoff2003": ("پوداساکف و همکاران", "Podsakoff et al.", 2003), "lawshe1975": ("لاوشه", "Lawshe", 1975), "polit2006": ("پولیت و بک", "Polit & Beck", 2006)}
for k, v in FAR.items(): CITE[k] = v["cite"]

VARS = [
 dict(code="COE", fa="فشار الزامی (قانونی و فرادستی)", cls=RB, refs=["dimaggio1983", "teo2003", "scott2014"], note="سازه و منطق گویه‌ها از طبقه‌بندی دی‌ماجیو و پاول (۱۹۸۳) و مقیاس‌های نهادی تئو و همکاران (۲۰۰۳) اقتباس و به بافت بودجه‌ریزی عملیاتی و گزارشگری تعهدی بازنویسی شده است.", scale=LIK, items=[
  ("COE1","قوانین و مقررات بالادستی، دستگاه ما را به اجرای مبنای تعهدی و بودجه‌ریزی عملیاتی ملزم کرده‌اند."),
  ("COE2","نهادهای نظارتی و دستگاه‌های فرادست بر اجرای این اصلاحات نظارت جدی دارند."),
  ("COE3","اجرا‌نکردن این اصلاحات پیامدهای قانونی یا اداری برای دستگاه دارد."),
  ("COE4","دستورالعمل‌ها و بخشنامه‌های ابلاغی شیوهٔ اجرای اصلاحات را به‌دقت تعیین می‌کنند.")]),
 dict(code="NOR", fa="فشار هنجاری (حرفه‌ای)", cls=RB, refs=["dimaggio1983", "teo2003", "scott2014"], note="اقتباس از همان منابع؛ گویه‌ها بر جامعهٔ حرفه‌ای، آموزش و هنجارهای همکاران تمرکز دارند.", scale=LIK, items=[
  ("NOR1","جامعهٔ حرفه‌ای حسابداری و حسابرسی دولتی، اجرای مبنای تعهدی را یک هنجار حرفه‌ای می‌داند."),
  ("NOR2","دوره‌های آموزشی و گردهمایی‌های حرفه‌ای، اجرای این اصلاحات را ترویج می‌کنند."),
  ("NOR3","همکاران و ذی‌حسابان باتجربه، اجرای دقیق این اصلاحات را یک ارزش حرفه‌ای می‌دانند."),
  ("NOR4","در مجامع علمی و حرفه‌ای، پیروی از استانداردهای حسابداری بخش عمومی امری مطلوب شمرده می‌شود.")]),
 dict(code="MIM", fa="فشار تقلیدی (الگوبرداری)", cls=RB, refs=["dimaggio1983", "teo2003", "oliver1991"], note="اقتباس از همان منابع با بازنویسی برای الگوبرداری از دستگاه‌های همتا و قالب‌های آمادهٔ مشاوران/نرم‌افزارها.", scale=LIK, items=[
  ("MIM1","دستگاه‌های مشابهِ موفق این اصلاحات را اجرا کرده‌اند و ما از الگوی آنان پیروی می‌کنیم."),
  ("MIM2","هرگاه دربارهٔ شیوهٔ اجرا ابهام داشته باشیم، روش دستگاه‌های همتا را الگو قرار می‌دهیم."),
  ("MIM3","بیشتر از قالب‌ها و گزارش‌های آمادهٔ مشاوران یا نرم‌افزارهای رایج استفاده می‌کنیم."),
  ("MIM4","نگرانیم اگر مانند سایر دستگاه‌ها عمل نکنیم، عقب‌مانده تلقی شویم.")]),
 dict(code="SUB", fa="اجرای ماهوی اصلاحات", cls=RM, refs=["pollitt2017", "moynihan2008", "christiaens2015", "pina2009"], note="مقیاس پیش‌تر منتشرشده‌ای که هم بودجه‌ریزی عملیاتی و هم گزارشگری تعهدی را به‌صورت «به‌کارگیری در تصمیم‌گیری» بسنجد یافت نشد؛ گویه‌ها بر پایهٔ ادبیات اصلاحات بخش عمومی نوشته شده‌اند.", scale=LIK, items=[
  ("SUB1","ارقام بودجه‌ای دستگاه بر پایهٔ برنامه‌ها و شاخص‌های عملکردی تدوین می‌شود."),
  ("SUB2","دستگاه بهای تمام‌شدهٔ فعالیت‌ها و خدمات را محاسبه می‌کند."),
  ("SUB3","صورت‌های مالی تعهدی به‌طور منظم و با فرایند کنترلی مشخص تهیه می‌شود."),
  ("SUB4","گزارش‌های مالی و عملکردی در جلسات مدیریتی بررسی می‌شود و اقدام اصلاحی بر پایهٔ آن‌ها انجام می‌گیرد."),
  ("SUB5","کارکنان مالی و مدیران برنامه مفاهیم این اصلاحات را درک می‌کنند و در کار روزمره به‌کار می‌گیرند.")]),
 dict(code="SYM", fa="انطباق نمادین (تشریفاتی)", cls=RM, refs=["meyer1977", "bromley2012", "oliver1991", "modell2009"], note="سازه از نظریهٔ جدایی (decoupling) و پذیرش تشریفاتی برگرفته است؛ گویه‌ها توسط پژوهشگر نوشته شده و نیازمند اعتبارسنجی‌اند.", scale=LIK, items=[
  ("SYM1","بیشتر گزارش‌های بودجهٔ عملیاتی صرفاً برای ارسال به مراجع فرادست تهیه می‌شود."),
  ("SYM2","شاخص‌های عملکردی به‌گونه‌ای تعیین می‌شوند که به‌آسانی محقق شوند."),
  ("SYM3","اجرای رسمی این اصلاحات در عمل بر نحوهٔ تخصیص و مصرف منابع تأثیری ندارد."),
  ("SYM4","اطلاعات تعهدی بیشتر برای تکمیل فرم‌ها و رعایت الزامات تنظیم می‌شود تا برای مدیریت.")]),
 dict(code="DIG", fa="بلوغ نظام اطلاعاتی مالی", cls=MIX, refs=["delone2003", "dunleavy2006"], note="ابعاد کیفیت سیستم و اطلاعات از مدل دلون و مک‌لین (۲۰۰۳) اقتباس و گویه‌های یکپارچگی، برخط‌بودن و ردپای حسابرسی را پژوهشگر افزوده است.", scale=LIK, items=[
  ("DIG1","سامانه‌های مالی دستگاه یکپارچه‌اند و داده‌ها بدون ورود مجدد منتقل می‌شوند."),
  ("DIG2","اطلاعات مالی و عملکردی به‌صورت برخط در دسترس مدیران است."),
  ("DIG3","سامانه‌ها ردپای ثبت و تغییرات (حسابرسی‌پذیری) را حفظ می‌کنند."),
  ("DIG4","کارکنان آموزش لازم برای استفادهٔ بهینه از سامانه‌ها را دیده‌اند.")]),
 dict(code="USE", fa="سودمندی اطلاعات گزارش‌شده برای تصمیم", cls=MIX, refs=["moynihan2010", "kroll2015", "delone2003"], note="مفهوم «استفاده از اطلاعات عملکرد» از موینیهان و پاندی (۲۰۱۰) و کرول (۲۰۱۵) اقتباس و برای اطلاعات مالی تعهدی بازنویسی شده است؛ گویه‌های USE3 و USE4 محقق‌ساخته‌اند.", scale=LIK, items=[
  ("USE1","اطلاعات گزارش‌شده مبنای تصمیم‌های مدیریتی (تخصیص و اولویت‌بندی) در دستگاه است."),
  ("USE2","گزارش‌ها به‌موقع و قابل‌فهم‌اند."),
  ("USE3","اطلاعات تعهدی نسبت به مبنای نقدی تصویر کامل‌تری از وضعیت مالی دستگاه ارائه می‌دهد."),
  ("USE4","اطلاعات گزارش‌شده برای ارزیابی کارایی و اثربخشی برنامه‌ها قابل‌اتکاست.")]),
 dict(code="ACC", fa="پاسخگویی مالی", cls=RM, refs=["bovens2007", "bracci2015", "moore1995"], note="ابعاد اطلاع‌رسانی، توجیه، و پیامد از چارچوب پاسخگویی بوونس (۲۰۰۷) استخراج شده و گویه‌ها محقق‌ساخته‌اند.", scale=LIK, items=[
  ("ACC1","دستگاه اطلاعات مالی و عملکردی را برای ذی‌نفعان (قوهٔ مقننه، نهادهای نظارتی و شهروندان) ارائه یا منتشر می‌کند."),
  ("ACC2","مدیران نتایج و انحرافات را به نهادهای نظارتی توضیح می‌دهند."),
  ("ACC3","در صورت انحراف از بودجه، مسئولیت مشخص و اقدام اصلاحی پیگیری می‌شود."),
  ("ACC4","یافته‌های حسابرسی و بازرسی در زمان معقول پیگیری و رفع می‌شود."),
  ("ACC5","اطلاعات ارائه‌شده از سوی دستگاه قابل راستی‌آزمایی است.")]),
]
DEMO = [("D1", "نوع دستگاه: وزارتخانه/سازمان ملی؛ دانشگاه و مراکز بهداشتی‌درمانی؛ شهرداری و نهادهای محلی؛ ادارات کل استانی"),
        ("D2", "سمت: مدیر مالی؛ ذی‌حساب؛ کارشناس بودجه؛ حسابدار/ حسابرس داخلی"), ("D3", "سابقهٔ کار در بخش عمومی (سال)"), ("D4", "سن (سال)"),
        ("D5", "تحصیلات: دیپلم و کمتر؛ کارشناسی؛ کارشناسی ارشد؛ دکتری")]
VALID = ["lawshe1975", "polit2006", "podsakoff2003"]
