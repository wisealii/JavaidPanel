<div align="center">

# JavaidPanel · جاوید پنل

**پنل مدیریت زیرساخت VPN، سرورها و نودها**

**JP UI** — طراحی اختصاصی مشکی، قرمز و سفید

![Version](https://img.shields.io/badge/version-1.1.104--dev-e84859?style=for-the-badge)
![Status](https://img.shields.io/badge/status-development-f0b66d?style=for-the-badge)
![License](https://img.shields.io/badge/license-GPL--3.0-eeeeee?style=for-the-badge)
![CI](https://github.com/wisealii/JavaidPanel/actions/workflows/verify.yml/badge.svg)

[**معرفی و مستندات**](docs/index.html) · [**دموی تصویری**](docs/demo.html) · [**نصب**](docs/INSTALLATION.md) · [**نودها**](docs/NODES.md) · [**امکانات**](docs/FEATURES.md) · [**رفع خطا**](docs/TROUBLESHOOTING.md)

</div>

---

## JavaidPanel چیست؟

**JavaidPanel** یک پروژهٔ متن‌باز برای مدیریت یکپارچهٔ زیرساخت VPN است: نصب و نگهداری سرویس مرکزی، پایش وضعیت، مدیریت کاربران و نودها و توسعهٔ آداپترهای پروتکل و تونل. طراحی ظاهری و نقشهٔ توسعهٔ آن با نام و هویت مستقل **JavaidPanel / JP UI** ارائه می‌شود.

> **مرحلهٔ توسعه:** نصب‌کنندهٔ یک‌دستوری و ابزارهای پایه موجودند، اما تست واقعیِ انتهابه‌انتها روی VPS، Javid Node اختصاصی، API تجاری و بسیاری از تونل‌ها هنوز تکمیل نشده‌اند. دمو فقط نمونهٔ رابط کاربری است و به سرور واقعی وصل نیست.

## نمای پروژه

| بخش | وضعیت | اطلاعات بیشتر |
|---|---|---|
| اسکریپت نصب یک‌دستوری | کد و تست ایستا موجود؛ VPS آزمایش نشده | [نصب](docs/INSTALLATION.md) |
| هسته مدیریت VPN | نصب‌کنندهٔ پایه با وابستگی‌های پین‌شده؛ نیازمند تست عملیاتی | [معماری](docs/ARCHITECTURE.md) |
| تنظیم گواهی HTTPS | ویزارد در مسیر هسته پایه؛ صدور واقعی آزمایش نشده | [SSL](docs/SSL.md) |
| نودهای پایه | کد یکپارچه‌سازی موجود؛ تست اتصال لازم | [نودها](docs/NODES.md) |
| Javid Node اختصاصی | در حال توسعه؛ نصب واقعی عامل مسدود | [اتصال نود](docs/NODE_ENROLLMENT.md) |
| اشتراک، تیکت، RBAC، فروش | طراحی/نمونه توسعه‌ای؛ API عملیاتی منتشر نشده | [امکانات](docs/FEATURES.md) |
| WireGuard / GRE / Rathole / Backhaul و سایر تونل‌ها | هر روش باید مستقل ساخته و روی دو VPS آزمایش شود | [کاتالوگ تونل](docs/TUNNELS.md) |
| دمو | رابط نمایشی بدون سرور و آمار واقعی | [دمو](docs/demo.html) |

## نصب آزمایشی با یک دستور

**فقط روی VPS آزمایشی تازه** با Ubuntu 24.04 یا Debian 12/13، `x86_64`، systemd و دسترسی sudo:

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash
```

اسکریپت، قبل از اجرای هسته، سیستم و وابستگی‌ها را بررسی می‌کند و فایل نصب پین‌شده را با SHA-256 تأیید می‌کند. **این دستور هنوز روی VPS واقعی در فرآیند توسعهٔ حاضر تأیید نشده است.**

### بررسی بدون تغییر سرور

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | bash -s -- --doctor
```

### بررسی سرویس و SSL بعد از نصب

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash -s -- --check
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash -s -- --ssl
```

برای حفاظت از سرور، پیش از اجرای اسکریپت‌های دانلودشده آن‌ها را بازبینی کنید. راهنمای کامل و شرایط موردنیاز در [نصب و راه‌اندازی](docs/INSTALLATION.md) قرار دارد.

## نمای ساختار مخزن

```text
JavaidPanel/
├── install.sh                   # بوت‌استرپ یک‌دستوری و کنترل نسخه/هش
├── installer/core.sh            # موتور پایه پین‌شده
├── node-agent-install.sh        # بررسی عامل نود؛ ثبت واقعی هنوز مسدود
├── docker-compose.production.yml # پیکربندی پیشنهادی؛ مستقل از مسیر نصب اصلی
├── docs/
│   ├── index.html               # وب‌سایت معرفی و مستندات
│   ├── demo.html                # دموی تعاملیِ کاملاً نمایشی
│   ├── FEATURES.md              # جدول امکانات و میزان تکمیل
│   ├── INSTALLATION.md          # نصب آزمایشی مرحله‌به‌مرحله
│   ├── SSL.md                   # دامنه و گواهی
│   ├── NODES.md                 # نودهای پایه و Javid Node
│   ├── NODE_ENROLLMENT.md       # طرح ثبت امن نود از داخل پنل
│   ├── TUNNELS.md               # کاتالوگ روش‌های تونل
│   ├── ARCHITECTURE.md          # معماری و مرز اجزا
│   ├── TROUBLESHOOTING.md       # عیب‌یابی
│   ├── DEVELOPMENT.md           # توسعه و تست
│   └── ROADMAP.md               # مراحل انتشار
├── tests/                       # آزمون‌های بدون نیاز به VPS
├── .github/workflows/verify.yml # بررسی خودکار
└── LICENSE / SOURCES.md         # مجوز و انتساب قانونی
```

## برای کاربران و توسعه‌دهندگان

**کاربر پنل:** از [راهنمای نصب](docs/INSTALLATION.md)، [SSL](docs/SSL.md) و [رفع اشکال](docs/TROUBLESHOOTING.md) شروع کن.

**مدیر چند VPS:** [راهنمای نود](docs/NODES.md) و [طرح «اتصال نود»](docs/NODE_ENROLLMENT.md) را بخوان؛ اتصال اختصاصی Javid Node هنوز در حال ساخت است.

**توسعه‌دهنده:** [راهنمای توسعه](docs/DEVELOPMENT.md)، [نقشه راه](docs/ROADMAP.md) و [ماتریس امکانات](docs/FEATURES.md) را بررسی کن.

## نسخه‌ها و انتشار

نسخه جاری **`1.1.104-dev`** است و به معنی نسخه پایدار نیست. هر انتشار پایدار باید تست نصب VPS، SSL، ارتقا، بکاپ/بازیابی و اتصال نود را پشت سر بگذارد. تغییرات: [CHANGELOG](CHANGELOG.md).

## مجوز

این پروژه همراه با بخش‌هایی از کد متن‌باز و وابستگی‌های دارای مجوز عرضه می‌شود. **هویت تجاری JavaidPanel مستقل است؛ اعلام منشأ کد و حفظ حق نشر الزامی است.** برای اطلاعات حقوقی و امنیتی [LICENSE](LICENSE)، [SOURCES.md](SOURCES.md) و [SECURITY.md](SECURITY.md) را ببینید.

---

<div align="center">JavaidPanel · JP UI · Build transparently, test before production.</div>
