# برنامهٔ ارتقای تجربهٔ نصب — الگوی NX / PasarGuard

در نسخه نهایی JavaidPanel باید تجربه نصب **به‌سادگی NX Panel** باشد و از وضوح مستندات PasarGuard الهام بگیرد، اما کد و طراحی هویت مستقل خود را حفظ کند.

## گام‌های UX
1. **سرور تازه**: بررسی معماری، نسخه OS، رم، پورت‌ها و نصب قبلی.
2. **نصب واقعی**: فقط پس از دانلود/ساخت و اعتبارسنجی backend و دیتابیس، اجرای سرویس و health check.
3. **ویزارد وب**: توکن راه‌اندازی کوتاه‌عمر و یک‌بارمصرف؛ ساخت مالک، آدرس پنل و TLS.
4. **گواهی**: آغاز با certificate داخلی self-signed، سپس صدور ACME معتبر دامنه و تمدید خودکار با reload اتمیک.
5. **ثبت نود**: شناسه + توکن enrollment یک‌بارمصرف، تأیید هویت متقابل، اتصال و گزارش سلامت واقعی.
6. **مدیریت**: status / logs / backup / restore / update / uninstall با کنترل آسیب.
7. **گزارش**: نسخه‌ها، آزمون‌ها، پورت‌های باز و خطرات نصب.

## معیار پذیرش
- نصب روی VPS تازه واقعاً dashboard را بالا بیاورد.
- health endpoint بدون وابستگی به پیام‌های ساختگی پاسخ دهد.
- SSL روی دامنه با browser verified chain فعال باشد.
- ثبت نود با کلید منقضی‌شده یا دوباره مصرف‌شده رد شود.
- قطع و وصل نود باعث حذف پیکربندی نشود.
- نصب مجدد از داده‌های قبلی محافظت کند.
- upgrade و rollback واقعاً تست شده باشند.

منابع:
- https://docs.nx-panel.org/fa/start/install-panel
- https://docs.nx-panel.org/fa/start/setup-wizard
- https://docs.nx-panel.org/fa/start/add-node
- https://docs.pasarguard.org/fa/
- https://docs.pasarguard.org/en/panel/installation/
