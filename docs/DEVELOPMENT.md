# راهنمای توسعه JavaidPanel

## شروع

```bash
git clone https://github.com/wisealii/JavaidPanel.git
cd JavaidPanel
bash -n install.sh
bash -n installer/core.sh
python3 -m unittest discover -s tests -p 'test_bootstrap.py' -v
bash install.sh --self-test
```

این آزمون‌ها **آفلاین و بدون root** هستند و به معنی تست نصب کامل نیستند.

## چیدمان

- `install.sh` بوت‌استرپ و کنترل SHA-256 هسته است.
- `installer/core.sh` یکپارچه‌سازی پایه پین‌شده؛ هنگام تغییر آن **هش در بوت‌استرپ و CI** باید هماهنگ شود.
- `node-agent-install.sh` فقط preflight است؛ افزودن daemon واقعی نیازمند طراحی امنیتی.
- `docs/index.html` و `docs/demo.html` صفحات استاتیک‌اند؛ جایگزین بک‌اند نیستند.
- `tests/` تست رگرسیون نصب‌کننده.
- `.github/workflows/verify.yml` CI.

## پیش‌نیاز هر Pull Request

1. تغییرات را با Issue و محدوده دقیق شرح بدهید.
2. اگر قابلیت جدید است، ماتریس `docs/FEATURES.md` را به‌روزرسانی کنید.
3. تست مربوطه اضافه کنید و در CI اجرا کنید.
4. هیچ credential، کلید، فایل env واقعی یا IP شخصی وارد Git نکنید.
5. برای پروتکل یا تونل، تست واقعی روی VPS آزمایشی و نحوه حذف/rollback ثبت کنید.
6. بخش‌های دارای مجوز، copyright و attribution را حفظ کنید.

## وضعیت نسخه و انتشار

- Development: پسوند `-dev` با changelog و CI.
- Release Candidate: فقط پس از تست نصب، ارتقا، SSL و نودها.
- Stable: فقط پس از بررسی امنیتی و تست واقعی با نسخه و checksum ثابت.

## بررسی‌های برنامه‌ریزی‌شده

- VM نصب Ubuntu/Debian و smoke test سلامت واقعی
- تست گواهی ACME در دامنه آزمایشی
- تست دو VPS برای ثبت نود
- تست backup/restore با داده
- تست اتصال پروتکل‌ها با client مستقل
- fuzz ورودی IP/پورت/توکن نود

[نقشه راه](ROADMAP.md) · [امنیت](../SECURITY.md)

## بررسی انسجام نسخه قبل از انتشار

```bash
python3 tools/verify-version-archive.py
python3 -m unittest discover -s tests -p 'test_version_archive.py' -v
```

[فرایند انتشار و آرشیو](RELEASING.md) · [نسخه‌ها](VERSIONS.md). پرونده‌های قدیمی توضیح تغییرات‌اند؛ برای کد دقیق هر نسخه به Git Tag معتبر نیاز داریم.
