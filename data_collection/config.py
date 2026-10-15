"""تنظیمات مشترک: شرایط غربالگری، endpointها و کلیدواژه‌های ردیف‌های صورت مالی."""
import pathlib
OUT = pathlib.Path("data_out"); OUT.mkdir(exist_ok=True)

# ---------- شرایط غربالگری (مطابق بخش ۴-۲ مقاله‌ها؛ قابل ویرایش) ----------
SCREEN = {
    "year_from": 1393, "year_to": 1402,
    "fiscal_year_end": "12/29",          # پایان سال مالی ۲۹ اسفند
    "min_consecutive_years": 3,
    "require_loans_any_year": True,      # حداقل در یک سال تسهیلات دریافتی/بازپرداخت دارد
    "min_total_assets": 0,               # در صورت تمایل حداقل دارایی (میلیون ریال)
    # صنایع حذف‌شونده (بر پایه نام گروه صنعت در TSETMC؛ پس از دیدن فهرست واقعی اصلاح شود)
    "exclude_sectors": ["بانک", "بیمه", "لیزینگ", "سرمایه گذاری", "سرمایه‌گذاری", "هلدینگ",
                        "واسطه گری مالی", "واسطه‌گری مالی", "فعالیتهای کمکی به نهادهای مالی",
                        "چند رشته ای صنعتی", "چند رشته‌ای صنعتی", "صندوق"],
    "only_audited": True,
}

# ---------- endpointها (در F12 تأیید شود) ----------
CODAL_SEARCH = "https://search.codal.ir/api/search/v2/q"
CODAL_BASE = "https://codal.ir"
CODAL_PARAMS = {"Audited": "true", "AuditorRef": "-1", "Category": "1", "Childs": "true",
                "CompanyState": "0", "CompanyType": "1", "Consolidatable": "true",
                "IsNotAudited": "false", "Length": "-1", "LetterType": "6", "Mains": "true",
                "NotAudited": "false", "NotConsolidatable": "true", "Publisher": "false",
                "TracingNo": "-1", "search": "true"}
TSE = "https://cdn.tsetmc.com/api"
TSE_ENDPOINTS = {
    "instrument": TSE + "/Instrument/GetInstrumentInfo/{ins}",
    "shareholders": TSE + "/Shareholder/GetInstrumentShareHolderLast/{ins}",
    "prices": TSE + "/ClosingPrice/GetClosingPriceDailyList/{ins}/0",
}
SLEEP = 1.5

# ---------- کلیدواژه ردیف‌ها (regex روی برچسب نرمال‌شده) و صفحه مربوط ----------
# sheet: bs=ترازنامه، is=سود و زیان، cf=جریان وجوه نقد
ITEMS = {
  "TA":        ("bs", r"^جمع دارایی"),
  "CA":        ("bs", r"^جمع دارایی های جاری"),
  "CL":        ("bs", r"^جمع بدهی های جاری"),
  "TL":        ("bs", r"^جمع بدهی ها$|^جمع بدهی"),
  "EQUITY":    ("bs", r"^جمع حقوق مالکانه|^جمع حقوق صاحبان سهام"),
  "CAPITAL":   ("bs", r"^سرمایه$"),
  "RETEARN":   ("bs", r"^سود \(زیان\) انباشته|^سود و زیان انباشته|^زیان انباشته|^سود انباشته"),
  "CASH":      ("bs", r"^موجودی نقد"),
  "INVENTORY": ("bs", r"^موجودی مواد و کالا"),
  "INTANG":    ("bs", r"^دارایی های نامشهود"),
  "PPE":       ("bs", r"^دارایی های ثابت مشهود"),
  "ST_INV":    ("bs", r"^سرمایه گذاری های کوتاه مدت"),
  "LT_INV":    ("bs", r"^سرمایه گذاری های بلند مدت"),
  "INV_PROP":  ("bs", r"^سرمایه گذاری در املاک|^املاک سرمایه گذاری"),
  "REL_REC":   ("bs", r"دریافتنی.*(اشخاص وابسته|وابسته)"),
  "LOAN_BAL":  ("bs", r"^تسهیلات مالی"),
  "SALES":     ("is", r"^درآمدهای عملیاتی|^فروش خالص"),
  "EBIT":      ("is", r"^سود \(زیان\) عملیاتی|^سود عملیاتی"),
  "FINCOST":   ("is", r"^هزینه های مالی"),
  "NI":        ("is", r"^سود \(زیان\) خالص|^سود خالص"),
  "CFO":       ("cf", r"فعالیت های عملیاتی"),
  "LOAN_IN":   ("cf", r"^دریافت تسهیلات مالی|^دریافت تسهیلات"),
  "LOAN_REPAY":("cf", r"^پرداخت اصل تسهیلات|^بازپرداخت اصل تسهیلات|^پرداخت تسهیلات"),
  "DEPRECIATION":("cf", r"^استهلاک"),
}
# اقلام یادداشتی که باید دستی/نیمه‌خودکار تکمیل شوند (فقط جست‌وجوی متنی در html):
NOTE_PATTERNS = {
  "OVERDUE": r"سررسید\s*گذشته",
  "PENALTY": r"جرائم\s*دیرکرد|جریمه\s*دیرکرد",
  "ART141": r"ماده\s*۱۴۱|ماده\s*141",
}
