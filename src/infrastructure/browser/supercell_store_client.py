import re
from typing import Optional

from playwright.sync_api import Page, Locator, expect


class SupercellStoreClient:
    """Клиент для навигации по Supercell Store через Playwright.

    Отвечает за открытие магазина игры, логин, выбор товара, переход к оплате
    и работу со страницей аккаунта (отвязка способа оплаты, логаут).
    Конкретные локаторы могут меняться, поэтому используются устойчивые
    паттерны по ролям/текстам, насколько это возможно.
    """

    def __init__(self, page: Page, base_url: str, game_slug: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.game_slug = game_slug.strip("/")

    # -------------------- Общие URL --------------------
    @property
    def game_url(self) -> str:
        return f"{self.base_url}/{self.game_slug}"

    # -------------------- Открытие магазина --------------------
    def open_store(self) -> None:
        """Открывает страницу игры в Supercell Store и ждёт загрузки."""

        self.page.goto(self.game_url)
        # Ожидаем, что URL содержит slug игры.
        expect(self.page).to_have_url(re.compile(self.game_slug, re.IGNORECASE))

    # -------------------- Логин --------------------
    def _login_button(self) -> Locator:
        """Возвращает локатор кнопки/ссылки входа."""

        return self.page.get_by_role(
            "link",
            name=re.compile("Log in|Войти", re.IGNORECASE),
        )

    def start_login(self, email: str) -> None:
        """Запускает процесс логина по email: открывает стор и запрашивает ОТП."""

        self.open_store()
        # Кликаем по кнопке входа Supercell ID.
        self._login_button().click()

        # Ждём появления поля ввода email (label или placeholder).
        email_input: Optional[Locator] = None

        candidate = self.page.get_by_role("textbox", name=re.compile("email", re.IGNORECASE))
        if candidate.count() > 0:
            email_input = candidate
        else:
            candidate = self.page.locator("input[type='email']")
            if candidate.count() > 0:
                email_input = candidate

        if email_input is None:
            raise RuntimeError("Не удалось найти поле ввода email на странице логина Supercell Store")

        email_input.fill(email)

        # Ищем кнопку перехода к вводу кода (Next/Continue).
        next_button = self.page.get_by_role(
            "button",
            name=re.compile("Next|Continue|Продолжить", re.IGNORECASE),
        )
        next_button.click()

    def complete_login_with_otp(self, otp_code: str) -> None:
        """Вводит ОТП-код из письма и завершает логин.

        Предполагается, что на экране уже открыта форма ввода кода после start_login.
        """

        # Пытаемся найти поле кода по label/названию.
        otp_input: Optional[Locator] = None

        candidate = self.page.get_by_role("textbox", name=re.compile("code|код", re.IGNORECASE))
        if candidate.count() > 0:
            otp_input = candidate
        else:
            # Fallback: поле ввода кода часто имеет тип tel или специальный autocomplete.
            candidate = self.page.locator("input[type='tel'], input[autocomplete*='one-time-code']")
            if candidate.count() > 0:
                otp_input = candidate

        if otp_input is None:
            raise RuntimeError("Не удалось найти поле ввода одноразового кода на странице логина Supercell Store")

        otp_input.fill(otp_code)

        # Подтверждаем вход.
        submit_button = self.page.get_by_role(
            "button",
            name=re.compile("Log in|Войти|Submit|Continue", re.IGNORECASE),
        )
        submit_button.click()

        # Ожидаем возврата в магазин игры (по URL/slug).
        expect(self.page).to_have_url(re.compile(self.game_slug, re.IGNORECASE))

    # -------------------- Этап 3: выбор товара и корзина --------------------
    def go_to_product_80_gems(self, product_url: Optional[str] = None) -> None:
        """Переходит к странице товара "80 гемов".

        - Если указан product_url (из config.yaml), используем его.
        - Иначе ищем карточку товара по названию/тексту на странице игры.
        """

        if product_url:
            self.page.goto(product_url)
            return

        # Если явного URL нет — убеждаемся, что мы на странице игры.
        self.open_store()

        # Пытаемся найти ссылку/кнопку товара по тексту, содержащему "80" и "gems".
        name_pattern = re.compile(r"80.*gem|80\s+гем", re.IGNORECASE)

        product_link = self.page.get_by_role("link", name=name_pattern)
        if product_link.count() == 0:
            # Fallback: ищем по тексту без роли.
            product_link = self.page.get_by_text(name_pattern)

        if product_link.count() == 0:
            raise RuntimeError("Не удалось найти товар '80 гемов' на странице магазина Supercell")

        product_link.first.click()

    def _ensure_quantity_one(self) -> None:
        """Пытается гарантировать, что количество товара в корзине = 1.

        Реализация максимально универсальна: сначала ищем input[type=number] и
        ставим '1'; если его нет — несколько раз нажимаем на кнопку уменьшения.
        """

        qty_input = self.page.locator("input[type='number']")
        if qty_input.count() > 0:
            qty_input.first.fill("1")
            return

        minus_button = self.page.get_by_role(
            "button",
            name=re.compile("-|minus|Decrease", re.IGNORECASE),
        )
        # Кликаем ограниченное число раз, чтобы не зациклиться.
        for _ in range(5):
            if minus_button.count() == 0:
                break
            minus_button.first.click()

    def add_to_cart_single_quantity(self) -> None:
        """Нажимает Buy и приводит количество к 1.

        Ожидается, что мы уже на странице товара.
        """

        buy_button = self.page.get_by_role(
            "button",
            name=re.compile("Buy|Купить", re.IGNORECASE),
        )
        buy_button.click()

        self._ensure_quantity_one()

    def proceed_to_checkout(self) -> None:
        """Переходит к странице Checkout и ждёт её загрузки."""

        with self.page.expect_navigation():
            checkout_button = self.page.get_by_role(
                "button",
                name=re.compile("Checkout|Перейти к оплате", re.IGNORECASE),
            )
            checkout_button.click()

        # Базовая проверка, что мы на странице оформления заказа.
        heading = self.page.get_by_role(
            "heading",
            name=re.compile("Checkout|Review your order|Оформление заказа", re.IGNORECASE),
        )
        expect(heading).to_be_visible()

    # -------------------- Этап 5: аккаунт, отвязка оплаты и логаут --------------------
    def open_account_page(self, account_url: Optional[str] = None) -> None:
        """Открывает страницу аккаунта Supercell Store.

        Если account_url передан из конфига, используется он, иначе собирается
        из base_url.
        """

        url = account_url or f"{self.base_url}/account"
        self.page.goto(url)

        # Проверяем, что на странице есть заголовок Account или блок с payment info.
        heading = self.page.get_by_role(
            "heading",
            name=re.compile("Account|Аккаунт", re.IGNORECASE),
        )
        if heading.count() == 0:
            payment_label = self.page.get_by_text(re.compile("Payment information", re.IGNORECASE))
            expect(payment_label).to_be_visible()
        else:
            expect(heading.first).to_be_visible()

    def detach_payment_method(self) -> None:
        """Отвязывает способ оплаты в разделе Payment information (best-effort).

        Реализация обобщённая: ищем блок с текстом Payment information, затем в нём
        кнопку удаления/отвязки. Если ничего не нашли, не падаем жёстко.
        """

        section = self.page.get_by_text(re.compile("Payment information", re.IGNORECASE))
        if section.count() == 0:
            # Ничего не нашли — возможно, способ оплаты уже не привязан.
            return

        container = section.nth(0).locator("xpath=ancestor::section | xpath=ancestor::div")

        remove_button = container.get_by_role(
            "button",
            name=re.compile("Remove|Удалить|Detach|Удалить карту", re.IGNORECASE),
        )
        if remove_button.count() == 0:
            # Fallback: любая кнопка с опасным действием внутри секции.
            remove_button = container.get_by_role("button")

        if remove_button.count() > 0:
            remove_button.first.click()

            # Подтверждение в модальном окне, если есть.
            confirm = self.page.get_by_role(
                "button",
                name=re.compile("Remove|Yes|Да|Confirm", re.IGNORECASE),
            )
            if confirm.count() > 0:
                confirm.first.click()

    def logout_supercell(self) -> None:
        """Выходит из аккаунта Supercell через ссылку/кнопку Log out.

        После выхода ожидаем появления кнопки входа на странице магазина.
        """

        logout = self.page.get_by_role(
            "link",
            name=re.compile("Log out|Выйти из аккаунта Supercell|Log Out", re.IGNORECASE),
        )
        if logout.count() == 0:
            # Fallback: кнопка вместо ссылки.
            logout = self.page.get_by_role(
                "button",
                name=re.compile("Log out|Выйти", re.IGNORECASE),
            )

        if logout.count() == 0:
            return

        logout.first.click()

        # Ожидаем, что снова появится кнопка "Log in".
        login_btn = self._login_button()
        expect(login_btn).to_be_visible()
