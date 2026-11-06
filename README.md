<div align="center">

# JAVID PANEL
### کنترل یکپارچهٔ زیرساخت VPN

**JavaidPanel · JP UI · Black / Red / White**

![Version](https://img.shields.io/badge/version-1.1.101-ef4351?style=for-the-badge) ![Status](https://img.shields.io/badge/status-development-f0b35b?style=for-the-badge) ![Theme](https://img.shields.io/badge/JP_UI-black%20%2B%20red%20%2B%20white-151519?style=for-the-badge)

[**صفحه معرفی**](docs/index.html) · [**راهنمای نصب**](docs/INSTALLATION.md) · [**مستندات نودها**](docs/NODES.md) · [**تونل‌ها**](docs/TUNNELS.md) · [**وضعیت پیاده‌سازی**](docs/STATUS.md)

</div>

---

## درباره JavaidPanel

**JavaidPanel** پروژه‌ای برای مدیریت زیرساخت VPN، سرورها، کاربران، اینباندها، نودهای توزیع‌شده و ابزارهای تونل است. هدف آن مدیریت یکپارچه، طراحی واضح و توسعه‌پذیری است.

نسخهٔ معرفی‌شده در سورس نصب‌کنندهٔ فعلی **1.1.101** است. بازطراحی ظاهری ریپازیتوری بر اساس هویت اختصاصی **JP UI** با رنگ‌های مشکی، قرمز و سفید انجام شده است.

> **مهم:** این مخزن تا زمان طی‌کردن آزمون‌های واقعی VPS نباید به‌عنوان نسخهٔ کاملاً پایدار معرفی شود. وجود گزینه یا پروتکل در توضیحات قبلی، به‌تنهایی تأیید عملکرد عملیاتی آن نیست.

## قابلیت‌ها و وضعیت

| بخش | وضعیت مشاهده‌شده در این بازطراحی |
|:---|:---|
| نصب‌کنندهٔ اصلی | `install.sh` در مخزن موجود است؛ حفظ شده |
| نصب عامل نود | `node-agent-install.sh` موجود است؛ حفظ شده |
| محیط Docker | `docker-compose.production.yml` موجود است؛ حفظ شده |
| مدیریت VPN و پروتکل‌ها | ادعاهای README قبلی؛ نیازمند تأیید کد و تست |
| نودهای چندسروری | اسکریپت عامل موجود؛ اتصال واقعی نیازمند تست |
| تونل‌های سرور به سرور | نیازمند بررسی پیاده‌سازی تک‌تک روش‌ها |
| صفحهٔ معرفی | طراحی ایستای اختصاصی در `docs/index.html` |
| تست نصب روی VPS | در این مرحله انجام نشده |

## شروع کار

برای دریافت مخزن و بررسی اولیهٔ اسکریپت‌ها:

```bash
git clone https://github.com/wisealii/JavaidPanel.git
cd JavaidPanel
bash -n install.sh
bash -n node-agent-install.sh
```

نصب روی VPS آزمایشی تنها **پس از مطالعه و بازبینی اسکریپت**:

```bash
sudo bash install.sh
```

**هرگز قبل از بازبینی کد، دستور دانلود و اجرای مستقیم با دسترسی root را صرفاً از روی یک تبلیغ اجرا نکنید.** اطلاعات پیش‌نیاز و هشدارها در [راهنمای نصب](docs/INSTALLATION.md) آمده است.

## نقشهٔ پروژه

```text
JavaidPanel/
├── README.md
├── VERSION
├── install.sh
├── node-agent-install.sh
├── docker-compose.production.yml
├── docs/
│   ├── index.html
│   ├── INSTALLATION.md
│   ├── NODES.md
│   ├── TUNNELS.md
│   ├── ARCHITECTURE.md
│   ├── STATUS.md
│   └── GITHUB_PAGES.md
└── .github/workflows/
    └── verify.yml
```

## رنگ‌بندی JP UI

- مشکی عمیق: `#0B0C10`
- قرمز جاوید: `#F04452`
- سفید کارت‌ها: `#FAFAFB`
- خاکستری زمینه: `#A5A5B2`

این طراحی برای **صفحهٔ GitHub Pages** است. تم استاندارد خود `github.com` را نمی‌توان به‌صورت اختصاصی برای یک مخزن تغییر داد.

## وضعیت و مسئولیت

بازطراحی صفحهٔ عمومی **بدون تغییر فایل‌های اصلی نصب‌کننده و عامل نود** تهیه شده است. پس از تست‌های سروری و بازبینی امنیتی، می‌توان انتشار نسخهٔ پایدار را برنامه‌ریزی کرد.

همهٔ وابستگی‌های متن‌باز و کدهای اقتباسی باید با رعایت مجوز و انتساب اصلی نگهداری شوند. به [یادداشت منابع و مجوزها](docs/LICENSING.md) مراجعه کنید.
