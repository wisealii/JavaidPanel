<div align="center">

# JavaidPanel

**سامانه مدیریت زیرساخت VPN و نودهای چندسروری**

**JP UI · مشکی / قرمز / سفید**

![Version](https://img.shields.io/badge/version-1.1.102--dev-f04452?style=for-the-badge)
![Install](https://img.shields.io/badge/installer-guarded-f5bd63?style=for-the-badge)
![Nodes](https://img.shields.io/badge/nodes-under%20development-848492?style=for-the-badge)

[صفحه معرفی و مستندات](docs/index.html) · [نصب](docs/INSTALLATION.md) · [مقایسه نصب](docs/INSTALL_UX.md) · [وضعیت واقعی](docs/STATUS.md)

</div>

## درباره پروژه

JavaidPanel پروژهٔ مدیریت سرورها، کاربران، تونل‌ها، نودها و زیرساخت VPN است. طراحی عمومی سایت با هویت JP UI ارائه شده و مسیر نصب هدف از تجربه NX Panel و PasarGuard الهام می‌گیرد.

## هشدار مهم درباره نسخه قبلی

در بازبینی نسخه `1.1.101` مشخص شد اسکریپت پنل فقط یک کانتینر Node با دستور `sleep infinity` اجرا می‌کند و اسکریپت نود هم سرویس نمایشی مشابهی بالا می‌آورد. این‌ها **نصب واقعی VPN Panel یا اتصال امن نود نیستند**.

برای جلوگیری از ادعای موفقیت نادرست، نسخه `1.1.102-dev` نصب ساختگی را متوقف می‌کند. **این نسخه هنوز آماده نصب و بهره‌برداری واقعی روی VPS نیست.**

## بررسی VPS، بدون تغییر سیستم

```bash
git clone https://github.com/wisealii/JavaidPanel.git
cd JavaidPanel
sudo bash install.sh --doctor
bash node-agent-install.sh --check
```

## دریافت گواهی مستقل

اگر دامنه و پیش‌نیازها درست است:

```bash
sudo bash install.sh --ssl panel.example.org
```

این فقط گواهی TLS می‌گیرد و **وب‌سرور نصب نمی‌کند**.

## معماری هدف

- نصب واقعی و بدون پرسش با یک دستور و لینک setup یک‌بارمصرف
- ویزارد گرافیکی برای مالک و آدرس و گواهی HTTPS
- ایجاد نود با توکن یک‌بارمصرف و اتصال احراز هویت‌شده
- مدیریت وضعیت، ارتقا و بکاپ با CLI
- مدیریت VPN، اشتراک، سرویس و کاربران پس از تکمیل هسته

**مستندات:** [نصب](docs/INSTALLATION.md) · [مقایسه با NX/PasarGuard](docs/INSTALL_UX.md) · [مدیریت نودها](docs/NODES.md) · [وضعیت واقعی](docs/STATUS.md)

فایل‌های Docker موجود نیز قبل از استفاده عملی باید بازبینی و تکمیل شوند. مجوزها و انتساب کدهای متن‌باز باید حفظ شود.
