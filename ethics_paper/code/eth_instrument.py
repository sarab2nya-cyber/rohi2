# -*- coding: utf-8 -*-
"""Instrument + references for the auditor-silence paper (Persian items, origin class, sources)."""
import sys
sys.path.insert(0, "../../gov_paper/code")
import importlib.util
_spec = importlib.util.spec_from_file_location("gov_instrument", "../../gov_paper/code/gov_instrument.py"); _g = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_g)
RB, RM, MIX, LIK = _g.RB, _g.RM, _g.MIX, _g.LIK
LAT = {k: v for k, v in _g.LAT.items() if k in ("fornell1981", "hu1999", "henseler2015", "marsh2004", "little2006", "preacher2008", "hayes2015", "maccallum1996", "igolkina2020", "podsakoff2003", "lawshe1975", "polit2006")}
LAT.update({
"bandura1999": "Bandura, A. (1999). Moral disengagement in the perpetration of inhumanities. //Personality and Social Psychology Review, 3//(3), 193–209. https://doi.org/10.1207/s15327957pspr0303_3",
"moore2012": "Moore, C., Detert, J. R., Klebe Treviño, L., Baker, V. L., & Mayer, D. M. (2012). Why employees do bad things: Moral disengagement and unethical organizational behavior. //Personnel Psychology, 65//(1), 1–48. https://doi.org/10.1111/j.1744-6570.2011.01237.x",
"detert2008": "Detert, J. R., Treviño, L. K., & Sweitzer, V. L. (2008). Moral disengagement in ethical decision making: A study of antecedents and outcomes. //Journal of Applied Psychology, 93//(2), 374–391. https://doi.org/10.1037/0021-9010.93.2.374",
"tenbrunsel2004": "Tenbrunsel, A. E., & Messick, D. M. (2004). Ethical fading: The role of self-deception in unethical behavior. //Social Justice Research, 17//(2), 223–236. https://doi.org/10.1023/B:SORE.0000027411.35832.53",
"victor1988": "Victor, B., & Cullen, J. B. (1988). The organizational bases of ethical work climates. //Administrative Science Quarterly, 33//(1), 101–125. https://doi.org/10.2307/2392857",
"morrison2000": "Morrison, E. W., & Milliken, F. J. (2000). Organizational silence: A barrier to change and development in a pluralistic world. //Academy of Management Review, 25//(4), 706–725. https://doi.org/10.5465/amr.2000.3707697",
"vandyne2003": "Van Dyne, L., Ang, S., & Botero, I. C. (2003). Conceptualizing employee silence and employee voice as multidimensional constructs. //Journal of Management Studies, 40//(6), 1359–1392. https://doi.org/10.1111/1467-6486.00384",
"jones1991": "Jones, T. M. (1991). Ethical decision making by individuals in organizations: An issue-contingent model. //Academy of Management Review, 16//(2), 366–395. https://doi.org/10.5465/amr.1991.4278958",
"trevino2006": "Treviño, L. K., Weaver, G. R., & Reynolds, S. J. (2006). Behavioral ethics in organizations: A review. //Journal of Management, 32//(6), 951–990. https://doi.org/10.1177/0149206306294258",
"kish2010": "Kish-Gephart, J. J., Harrison, D. A., & Treviño, L. K. (2010). Bad apples, bad cases, and bad barrels: Meta-analytic evidence about sources of unethical decisions at work. //Journal of Applied Psychology, 95//(1), 1–31. https://doi.org/10.1037/a0017103",
"bazerman2012": "Bazerman, M. H., & Gino, F. (2012). Behavioral ethics: Toward a deeper understanding of moral judgment and dishonesty. //Annual Review of Law and Social Science, 8//, 85–104. https://doi.org/10.1146/annurev-lawsocsci-102811-173815",
"near1985": "Near, J. P., & Miceli, M. P. (1985). Organizational dissidence: The case of whistle-blowing. //Journal of Business Ethics, 4//(1), 1–16. https://doi.org/10.1007/BF00382668",
"lewis2001": "Lewis, M. K. (2001). Islam and accounting. //Accounting Forum, 25//(2), 103–127. https://doi.org/10.1111/1468-5879.00007",
"baydoun2000": "Baydoun, N., & Willett, R. (2000). Islamic corporate reports. //Abacus, 36//(1), 71–90. https://doi.org/10.1111/1467-6281.00055",
"malone1996": "Malone, C. F., & Roberts, R. W. (1996). Factors associated with the incidence of reduced audit quality behaviors. //Auditing: A Journal of Practice & Theory, 15//(2), 49–64.",
"dezoort1997": "DeZoort, F. T., & Lord, A. T. (1997). A review and synthesis of pressure effects research in accounting. //Journal of Accounting Literature, 16//, 28–85.",
})
FAR = {
"mehrani1382": dict(fa="مهرانی، ساسان و نعیمی، ==[نام کوچک]== (۱۳۸۲). تئوری اخلاقی و تأثیر فشار بودجهٔ زمانی بر رفتار حسابرسان مستقل. //بررسی‌های حسابداری و حسابرسی، ۱۰//(۲)، ۴۳-۶۱.",
   en="Mehrani, S., & Naimi, ==[first name]== (2003). Moral theory and the effect of time budget pressure on the behavior of independent auditors. //Accounting and Auditing Review, 10//(2), 43–61. (in Persian)", cite=("مهرانی و نعیمی", "Mehrani & Naimi", 1382)),
"kahesh1401": dict(fa="==[نویسندگان]== (۱۴۰۱). بررسی تأثیرهای فشار زمانی، تعارض کار-خانواده و ابهام نقش بر رفتارهای کاهندهٔ کیفیت حسابرسی با میانجی‌گری استرس شغلی. //بررسی‌های حسابداری و حسابرسی، ۲۹//(۴)، ۷۱۴-۷۳۷. https://doi.org/10.22059/acctgrev.2023.344298.1008693",
   en="==[Authors]== (2022). The effects of time pressure, work–family conflict and role ambiguity on audit quality reduction behaviors with the mediating role of job stress. //Accounting and Auditing Review, 29//(4), 714–737. https://doi.org/10.22059/acctgrev.2023.344298.1008693 (in Persian)", cite=("نویسندگان بررسی‌های حسابداری و حسابرسی", "Authors", 1401)),
"mahdavi": dict(fa="مهدوی، غلامحسین؛ بهمنی، رضا و نمازی، نویدرضا (==[سال]==). نقش میانجی‌گری رفتار ناکارآمد حسابرس در تبیین رابطهٔ بین دین‌داری و تعهد حرفه‌ای با کیفیت حسابرسی. //حسابداری ارزشی و رفتاری، ==[دوره]==//(==[شماره]==)، ==[صفحات]==.",
   en="Mahdavi, G., Bahmani, R., & Namazi, N. R. (==[year]==). The mediating role of dysfunctional auditor behavior in explaining the relationship between religiosity and professional commitment with audit quality. //Journal of Value and Behavioral Accounting, ==[vol.]==//(==[no.]==), ==[pages]==. (in Persian)", cite=("مهدوی، بهمنی و نمازی", "Mahdavi, Bahmani, & Namazi", 1400)),
"ebrahimi1401": dict(fa="ابراهیمی، ==[نام]==؛ صفری گرایلی، ==[نام]== و ولیان، ==[نام]== (۱۴۰۱). طراحی مدل علل تقویت‌کنندهٔ سکوت سازمانی حسابرسان داخلی. //پژوهش‌های تجربی حسابداری، ==[دوره]==//(==[شماره]==)، ==[صفحات]==.",
   en="Ebrahimi, ==[first name]==, Safari Gerayeli, ==[first name]==, & Valian, ==[first name]== (2022). Designing a model of the causes that reinforce internal auditors' organizational silence. //Empirical Studies in Accounting Research, ==[vol.]==//(==[no.]==), ==[pages]==. (in Persian)", cite=("ابراهیمی، صفری گرایلی و ولیان", "Ebrahimi, Safari Gerayeli, & Valian", 1401)),
}
CITE = {
"bandura1999": ("بندورا", "Bandura", 1999), "moore2012": ("مور و همکاران", "Moore et al.", 2012), "detert2008": ("دترت، ترونیو و سوایتزر", "Detert, Treviño, & Sweitzer", 2008),
"tenbrunsel2004": ("تنبرانسل و مسیک", "Tenbrunsel & Messick", 2004), "victor1988": ("ویکتور و کالن", "Victor & Cullen", 1988), "morrison2000": ("موریسون و میلیکن", "Morrison & Milliken", 2000),
"vandyne2003": ("ون‌داین، آنگ و بوترو", "Van Dyne, Ang, & Botero", 2003), "jones1991": ("جونز", "Jones", 1991), "trevino2006": ("ترونیو، ویور و رینولدز", "Treviño, Weaver, & Reynolds", 2006),
"kish2010": ("کیش‌گفارت، هریسون و ترونیو", "Kish-Gephart, Harrison, & Treviño", 2010), "bazerman2012": ("بازرمن و جینو", "Bazerman & Gino", 2012), "near1985": ("نیر و میسلی", "Near & Miceli", 1985),
"lewis2001": ("لوئیس", "Lewis", 2001), "baydoun2000": ("بیدون و ویلت", "Baydoun & Willett", 2000), "malone1996": ("مالون و رابرتس", "Malone & Roberts", 1996), "dezoort1997": ("دیزورت و لرد", "DeZoort & Lord", 1997),
"fornell1981": ("فورنل و لارکر", "Fornell & Larcker", 1981), "hu1999": ("هو و بنتلر", "Hu & Bentler", 1999), "henseler2015": ("هنسلر، رینگل و سارستدت", "Henseler, Ringle, & Sarstedt", 2015),
"marsh2004": ("مارش، ون و هائو", "Marsh, Wen, & Hau", 2004), "little2006": ("لیتل، بووایرد و ویدمن", "Little, Bovaird, & Widaman", 2006), "preacher2008": ("پریچر و هیز", "Preacher & Hayes", 2008),
"hayes2015": ("هیز", "Hayes", 2015), "maccallum1996": ("مک‌کالوم، براون و سوگاوارا", "MacCallum, Browne, & Sugawara", 1996), "igolkina2020": ("ایگولکینا و مشچریاکوف", "Igolkina & Meshcheryakov", 2020),
"podsakoff2003": ("پوداساکف و همکاران", "Podsakoff et al.", 2003), "lawshe1975": ("لاوشه", "Lawshe", 1975), "polit2006": ("پولیت و بک", "Polit & Beck", 2006)}
for k, v in FAR.items(): CITE[k] = v["cite"]
VARS = [
 dict(code="TBP", fa="فشار بودجهٔ زمانی", cls=RM, refs=["dezoort1997", "malone1996", "mehrani1382"], scale=LIK, note="مقیاس منتشرشدهٔ هم‌خوان با بافت مؤسسات حسابرسی ایران یافت نشد؛ گویه‌ها بر پایهٔ مفهوم فشار بودجهٔ زمانی در ادبیات (دیزورت و لرد؛ مالون و رابرتس؛ مهرانی و نعیمی) نوشته شده‌اند.", items=[
  ("TBP1","بودجهٔ زمانی تعیین‌شده برای کارهای حسابرسی من معمولاً کمتر از زمان لازم برای انجام دقیق آن‌هاست."),
  ("TBP2","مهلت‌های تحویل کار در مؤسسهٔ ما به‌گونه‌ای است که فرصت کافی برای بررسی دقیق باقی نمی‌گذارد."),
  ("TBP3","عملکرد من بیش از هر چیز بر پایهٔ رعایت بودجهٔ زمانی ارزیابی می‌شود."),
  ("TBP4","در فصل اوج کار، حجم کار آن‌قدر است که فرصت تأمل در یافته‌های غیرمعمول را ندارم.")]),
 dict(code="ECL", fa="جو اخلاقی سازمان", cls=RB, refs=["victor1988", "kish2010"], scale=LIK, note="اقتباس از پرسشنامهٔ جو اخلاقی ویکتور و کالن (۱۹۸۸) با سه بُعد توجه به دیگران، قواعد و قانون/آیین‌نامه و پیگیری امن نگرانی‌های اخلاقی؛ گویه‌ها بازنویسی و کوتاه شده‌اند.", items=[
  ("ECL1","در مؤسسهٔ ما همکاران به منافع یکدیگر و ذی‌نفعان توجه واقعی دارند."),
  ("ECL2","در مؤسسهٔ ما از همه انتظار می‌رود پیش از هر چیز قوانین و استانداردهای حرفه‌ای را رعایت کنند."),
  ("ECL3","رفتار اخلاقی مدیران ارشد مؤسسهٔ ما الگوی عملی برای دیگران است."),
  ("ECL4","در مؤسسهٔ ما کسی که نگرانی اخلاقی مطرح می‌کند تنبیه نمی‌شود.")]),
 dict(code="CON", fa="وجدان حرفه‌ای", cls=RM, refs=["lewis2001", "baydoun2000", "mahdavi"], scale=LIK, note="سازه به درونی‌سازی ارزش‌های اخلاقی و حرفه‌ای (امانت‌داری، پاسخگویی در برابر وجدان و خداوند، تقدم نفع عمومی) اشاره دارد که در ادبیات اخلاق اسلامی در حسابداری (لوئیس؛ بیدون و ویلت) مطرح شده است؛ مقیاس استانداردی با این تعریف نیست و گویه‌ها محقق‌ساخته‌اند.", items=[
  ("CON1","حفظ امانت‌داری در برابر استفاده‌کنندگان از گزارش را وظیفه‌ای وجدانی می‌دانم، حتی اگر کسی بر آن نظارت نکند."),
  ("CON2","خود را در برابر وجدان و باورهای اخلاقی‌ام پاسخگوی نتایج کارم می‌دانم."),
  ("CON3","نفع عمومی را بر آسایش شخصی و سازمانی مقدم می‌دارم."),
  ("CON4","ارزش‌های اخلاقی‌ام در تصمیم‌های حرفه‌ای من نقش تعیین‌کننده دارد.")]),
 dict(code="MD", fa="رفع تعهد اخلاقی", cls=RB, refs=["bandura1999", "moore2012", "detert2008"], scale=LIK, note="اقتباس از مقیاس گرایش به رفع تعهد اخلاقی مور و همکاران (۲۰۱۲) و دترت و همکاران (۲۰۰۸) برای پنج سازوکار توجیه اخلاقی، برچسب‌زنی تلطیف‌شده، مقایسهٔ سودمند، جابه‌جایی و پخش مسئولیت؛ گویه‌ها با بافت حسابرسی بازنویسی شده‌اند.", items=[
  ("MD1","اگر هدف خوبی در میان باشد (مثل حفظ صاحبکار یا رعایت زمان‌بندی)، چشم‌پوشی از اشکال‌های کوچک را موجه می‌دانم."),
  ("MD2","به برخی اشتباهات می‌توان نام «تفاوت سلیقه در برآورد» داد و آن‌ها را جدی نگرفت."),
  ("MD3","در مقایسه با تخلف‌های بزرگی که در حرفه دیده می‌شود، بعضی انحرافات کوچک اهمیتی ندارد."),
  ("MD4","اگر مدیر ارشد تصمیم بگیرد، مسئولیت پیامد با او است، نه با من."),
  ("MD5","وقتی همهٔ اعضای تیم یک رویه را می‌پذیرند، مسئولیت فردی من برای مخالفت کمرنگ می‌شود.")]),
 dict(code="SIL", fa="سکوت دربارهٔ تخلف کشف‌شده", cls=RB, refs=["morrison2000", "vandyne2003", "near1985", "ebrahimi1401"], scale=LIK, note="اقتباس از ابعاد سکوت تسلیم‌شده و سکوت دفاعی ون‌داین و همکاران (۲۰۰۳) و مفهوم سکوت سازمانی (موریسون و میلیکن، ۲۰۰۰) با بازنویسی برای وضعیت مشاهدهٔ ناهنجاری در مدارک صاحبکار. نمرهٔ بالاتر یعنی سکوت بیشتر.", items=[
  ("SIL1","اگر ناهنجاری مشکوکی در مدارک صاحبکار ببینم، ترجیح می‌دهم موضوع را با سرپرست مطرح نکنم."),
  ("SIL2","اگر نگران پیامدهای شخصی باشم، دربارهٔ یافتهٔ مشکوک سکوت می‌کنم."),
  ("SIL3","معمولاً موضوعات حساس را در گزارش‌های کاری نمی‌آورم تا درگیری پیش نیاید."),
  ("SIL4","فکر می‌کنم طرح مسئله تغییری ایجاد نمی‌کند، بنابراین ساکت می‌مانم."),
  ("SIL5","برای حفظ موقعیت شغلی‌ام دربارهٔ اشکال‌های مشاهده‌شده سخن نمی‌گویم.")]),
]
DEMO = [("D1", "جنسیت"), ("D2", "سن (سال)"), ("D3", "سابقهٔ کار حسابرسی (سال)"), ("D4", "رتبهٔ سازمانی: حسابرس مقدماتی؛ حسابرس ارشد؛ سرپرست؛ مدیر/شریک"), ("D5", "محل کار: سازمان حسابرسی؛ مؤسسهٔ حسابرسی خصوصی؛ سایر"), ("D6", "تحصیلات: کارشناسی؛ کارشناسی ارشد؛ دکتری"), ("D7", "عضویت در جامعهٔ حسابداران رسمی (بله/خیر)")]
