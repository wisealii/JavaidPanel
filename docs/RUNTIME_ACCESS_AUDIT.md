# ممیزی اولیه Gateway، TLS، Subscription و دسترسی‌ها

تاریخ: ۲۰۲۶-۱۱-۱۰. مبنا: JavaidPanel `1.1.113-dev`، Commit `0d23d7458801d1b984d5d660ad0491cefed125ce`.
این سند شواهد سورس و مشاهده را از آزمون عملی مجوزها جدا می‌کند. اطلاعات اتصال و اسرار درج نشده‌اند.

## TLS و Subscription

در بررسی فقط‌خواندنی VPS، سه سرویس اصلی active بودند و هش Gateway/brand/theme با خروجی embedded مبنا تطبیق داشت. TLS عمومی domain است؛ VPN backend روی loopback:18080 و بدون webCertFile کار می‌کند. بنابراین HTTP داخلی به معنی HTTP عمومی نیست. [Issue 28](https://github.com/wisealii/JavaidPanel/issues/28) اختلاف نمایش SSL Manager را پیگیری می‌کند؛ صدور یا تغییر گواهی اجرا نشده است.

در سورس `Features.defaults` گواهی Gateway به فرم‌های بومی معرفی می‌شود؛ این معرفی به معنی ثبت در فهرست مستقل SSL Manager نیست. `tls.py` تمدید Gateway را مدیریت می‌کند.

هشدار UI مسیرهای پیش‌فرض Subscription مشاهده شد. در سورس بالادستی `web/html/settings.html` شرط هشدار با مقایسه pathname با `/sub/` و `/json/` ساخته می‌شود. این شرط به‌تنهایی افشای داده یا ضعف توکن را ثابت نمی‌کند. `web/service/setting.go` همین پیش‌فرض‌ها را دارد. در Gateway، `Features.defaults` در نبود URI سفارشی لینک‌های همان HTTPS Gateway را می‌دهد و `Nodes.sub_target` شناسه و مسیر را اعتبارسنجی کرده، درخواست را به سرویس اشتراک هدایت می‌کند. URI سفارشی حفظ می‌شود.

بررسی تصادفی‌بودن شناسه‌ها، دسترسی اینترنتی و کنترل حساب‌های متفاوت هنوز انجام نشده است. هیچ مسیر اشتراکی تغییر نکرده؛ تغییر شتاب‌زده می‌تواند کلاینت‌های موجود را قطع کند. فعلاً این مورد توصیه تنظیماتی/نیازمند بررسی است، نه آسیب‌پذیری اثبات‌شده P0/P1.

## ماتریس دسترسی از سورس

منابع JavaidPanel: `installer/core.sh`، متدهای `Gateway.is_admin`، `dispatch` و routeهای Nodes/Features/Insights/DNSClients.
منابع بالادستی مشاهده‌شده در ref `v1.9.4` مخزن Sir-MmD/vpn-ui: `database/model/permission.go` و `web/controller/{permission,admin,server}.go`.
تطابق کامل این ref با باینری نصب‌شده اثبات نشده؛ جدول زیر قرارداد خوانده‌شده است و تست حساب‌های محدود جای آن را نمی‌گیرد.

| قابلیت | Super Admin | مدیر/پشتیبان واگذارشده | نماینده | کاربر نهایی |
|---|---|---|---|---|
| داشبورد | مجاز در سورس | accessOverview | grant نمایه | دسترسی مدیریتی تأیید نشده |
| مدیریت از Overview | مجاز | manageOverview و در مواردی مجوز عمل | grant نمایه با access | تأیید نشده |
| ساخت/ویرایش/حذف Inbound | مجاز | bit مربوط و grant ورودی | mask نقش شامل این bitها نیست | تأیید نشده |
| کلاینت | مجاز | bit مربوط و grant ورودی/حساب | mask مشتق نقش و مالکیت حساب | اشتراک شخصی؛ آزمون نشده |
| تنظیمات Xray/Core/Panel | مجاز | accessXraySettings / accessCoreSettings / accessPanelSettings | در mask پایه نیست | تأیید نشده |
| مدیریت مدیران | مجاز | رد توسط requireSuperAdmin | رد توسط requireSuperAdmin | رد طبق همان gate |
| مدیریت نمایندگان | مجاز | manageResellers | در mask پایه نیست | تأیید نشده |
| DB export/import، لاگ، config و update از Overview | مجاز | manageOverview؛ دسترسی بسیار حساس | طبق grant مدیریت Overview | تأیید نشده |
| DNS/Nodes/Content یکپارچه | Gateway.is_admin | endpoint مجوز مدیران gate دارد؛ نیازمند آزمون منفی واقعی | نیازمند آزمون منفی واقعی | نیازمند آزمون منفی واقعی |
| SSL بومی | تابع routeهای backend؛ پوشش کامل بررسی نشده | بررسی تکمیلی لازم | بررسی تکمیلی لازم | تأیید نشده |
| reboot، systemd و مدیریت مدیران | gateهای Super Admin طبق سورس | نباید از مجوز Overview نتیجه گرفته شود | همان | همان |

`Gateway.is_admin` پاسخ JSON با success:true و فهرست غیرخالی از `panel/admins/permissions` را می‌پذیرد؛ در سورس backend مشاهده‌شده، گروه AdminController با requireSuperAdmin محافظت شده است. این وابستگی باید با حساب‌های واقعی محدود تست شود.

نکته مهم: توضیحات قدیمی بعضی فایل‌های بالادستی می‌گویند backup/logs فقط Super Admin است، اما routeهای server.go اکنون برای getDb، importDB، logs و update از requireOverviewManage استفاده می‌کنند. مستندات را از روی نام نقش یا پنهان‌بودن منو نتیجه‌گیری نکنید. این اختیار موجود را بدون تصمیم مالک تغییر ندهید.

پشتیبان در این ممیزی نقش مستقل اثبات‌شده نیست؛ می‌تواند یک حساب مدیر با مجوزهای محدود باشد. کنترل چهار دستگاه، سهمیه روزانه و سیاست‌های تجاری Free/Premium هنوز از سورس اثبات و عملیاتی نشده‌اند. RBAC یا سیستم اشتراک جدید ساخته نشده است.

## موجودی قابلیت‌ها و آزمون

| دسته | شاهد سورس اصلی | وضعیت |
|---|---|---|
| داشبورد/پایش | Gateway و backend VPN-UI | رابط مشاهده شد؛ صحت همه شمارنده‌ها آزمون نشده |
| کاربران/حساب | Admins/Clients backend | نشست مدیر مشاهده شد؛ حساب محدود تست نشده |
| اشتراک/سهمیه | nodes.py، subscriber.py، Features.defaults | سورس موجود؛ سناریوی کلاینت آزمون نشده |
| سرور/نود | nodes.py، nodes.html، nodes.js | UI موجود؛ نود دوم فراهم نیست |
| پروتکل/کانفیگ | backend پین‌شده و Xray | Xray Running مشاهده شد؛ اتصال بیرونی آزمون نشده |
| VPN/DNS/شبکه | Gateway، AdGuard، dns_clients.py | سرویس و DNS داخلی قبلاً موفق؛ DNS بیرونی آزمون نشده |
| امنیت/SSL | tls.py، Gateway.validate_origin، backend permissions | HTTPS قبلاً موفق؛ تمدید و منفی‌های مجوز آزمون نشده |
| بکاپ/بازیابی | CLI backup در core | بکاپ محلی قبلاً موفق؛ restore جدا آزمون نشده |
| گزارش/لاگ | insights.py، backend logs | سورس/UI موجود؛ داده زنده کلاینت آزمون نشده |
| تنظیمات | backend settings، Features.defaults | صفحات مشاهده شد؛ ذخیره تنظیمات حساس اجرا نشده |
| نگهداری | manage.py، CLI و tools | سلامت مبنا قبلاً موفق؛ repair/upgrade/reboot اجرا نشده |

## ادامه کار و محدودیت‌ها

- برای تست محدودیت نقش‌ها، حساب آزمایشی و مجوز مالک لازم است؛ هنوز ایجاد نشده است.
- ایجاد Inbound/Client و تست ترافیک بیرونی و restore باید طبق مجوز مشخص و محیط مناسب انجام شود.
- سورس اپ مستقل Javaid VPN برای این مرحله ارائه نشده؛ اتصال کلاینت پیاده‌سازی‌شده ادعا نمی‌شود.
- [PR 27](https://github.com/wisealii/JavaidPanel/pull/27) فقط شخصی‌سازی لایه نمایش و تست سازگاری است؛ این ممیزی هیچ مجوزی را تغییر نمی‌دهد.
