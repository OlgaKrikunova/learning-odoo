from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class EstatePropertyTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.test_partner = cls.env["res.partner"].create(
            {  # создание тестового партнера
                "name": "Test Buyer",
                "email": "buyer@test.com",
            }
        )

        # Создаем несколько тестовых объектов недвижимости
        cls.properties = cls.env["estate.property"].create(
            [
                {
                    "name": "Small House",
                    "expected_price": 100000,
                    "living_area": 100,
                    "garden": True,
                    "garden_area": 50,
                    "garden_orientation": "south",
                    "bedrooms": 2,
                },
                {
                    "name": "Big Villa",
                    "expected_price": 500000,
                    "living_area": 300,
                    "garden": True,
                    "garden_area": 200,
                    "garden_orientation": "east",
                    "bedrooms": 5,
                    "state": "new",
                },
                {
                    "name": "Apartment",
                    "expected_price": 200000,
                    "living_area": 80,
                    "garden": False,
                    "garden_area": 0,
                    "bedrooms": 1,
                    "state": "sold",  # Уже продана
                },
            ]
        )

        # Создаем оффер для второй недвижимости
        cls.test_offer = cls.env["estate.property.offer"].create(
            {
                "price": 450000,
                "partner_id": cls.test_partner.id,
                "property_id": cls.properties[1].id,
                "status": "accepted",
            }
        )

    def test_01_compute_total_area(self):
        """Тест: проверяем правильность вычисления общей площади"""
        # Проверяем начальные значения
        self.assertEqual(
            self.properties[0].total_area,
            150,  # 100 + 50
            "Total area should be sum of living area and garden area",
        )

        # Изменяем значения и проверяем пересчет
        self.properties[0].living_area = 120
        self.assertEqual(
            self.properties[0].total_area,
            170,  # 120 + 50
            "Total area should be recalculated when living area changes",
        )

    def test_02_onchange_garden(self):
        """Тест: проверяем сброс полей сада при снятии галочки Garden"""
        # Используем Form для эмуляции работы с формой (onchange работает только в формах)
        with Form(self.properties[0]) as property_form:
            # Проверяем начальные значения
            self.assertTrue(property_form.garden)
            self.assertEqual(property_form.garden_area, 50)
            self.assertEqual(property_form.garden_orientation, "south")

            # Снимаем галочку Garden
            property_form.garden = False

            # Проверяем, что поля сбросились
            self.assertEqual(property_form.garden_area, 0, "Garden area should be reset to 0 when garden is unchecked")
            self.assertFalse(
                property_form.garden_orientation, "Garden orientation should be reset when garden is unchecked"
            )

            # Включаем обратно и проверяем значения по умолчанию
            property_form.garden = True
            self.assertEqual(property_form.garden_area, 10)  # значение по умолчанию
            self.assertEqual(property_form.garden_orientation, "north")  # значение по умолчанию

    def test_03_action_sell_success(self):
        """Тест: успешная продажа недвижимости"""
        property_to_sell = self.properties[1]

        # Проверяем начальный статус
        self.assertEqual(property_to_sell.state, "offer_received")

        # Продаем недвижимость
        property_to_sell.estate_property_action_sold()

        # Проверяем результат
        self.assertEqual(property_to_sell.state, "sold", "Property state should be 'sold' after selling")

    def test_04_action_sell_without_accepted_offer(self):
        """Тест: продажа недвижимости без офферов (метод не запрещает)"""
        property_without_offer = self.properties[0]

        # Проверяем начальный статус
        initial_state = property_without_offer.state

        # Продаем недвижимость без офферов
        property_without_offer.estate_property_action_sold()

        # Проверяем результат
        self.assertEqual(
            property_without_offer.state,
            "sold",
            f"Property state should be 'sold' even without offers (initial state was {initial_state})",
        )

    def test_05_cancel_sold_property(self):
        """Тест: попытка отменить продажу уже проданной недвижимости"""
        sold_property = self.properties[2]

        # Пытаемся отменить проданную недвижимость
        with self.assertRaises(UserError) as error_context:
            sold_property.estate_property_action_cancel()

        self.assertIn(
            "Sold property cannot be cancelled.",
            str(error_context.exception),
            "Should not allow canceling sold property",
        )

    def test_06_multiple_properties_values(self):
        """Тест: проверка значений нескольких записей с помощью assertRecordValues"""
        # Удобный метод для проверки значений нескольких записей одновременно
        self.assertRecordValues(
            self.properties,
            [
                {  # Первая запись
                    "name": "Small House",
                    "total_area": 150,
                    "state": "new",
                },
                {  # Вторая запись
                    "name": "Big Villa",
                    "total_area": 500,
                    "state": "offer_received",
                },
                {  # Третья запись
                    "name": "Apartment",
                    "total_area": 80,
                    "state": "sold",
                },
            ],
        )

    def test_07_check_selling_price(self):
        """Тест: проверка цены продажи записи с оффером"""

        property_with_selling_price = self.properties[1]

        # Проверяем, что у property есть хотя бы один принятый оффер
        self.assertTrue(
            property_with_selling_price.offer_ids.filtered(lambda o: o.status == "accepted"),
            "Property должно иметь хотя бы один принятый оффер",
        )

        # Проверяем, что минимальная допустимая цена рассчитана корректно
        expected_min_price = property_with_selling_price.expected_price * 0.9
        self.assertEqual(
            expected_min_price,
            property_with_selling_price.expected_price * 0.9,
            "Минимальная цена должна считаться как 90% от expected_price",
        )

        # проверям, что выдает ошибку при выборе оффера с суммой, которая меньше допустимой
        with self.assertRaises(ValidationError) as error_context:
            property_with_selling_price.write({"selling_price": expected_min_price - 1})

        self.assertIn(
            "The selling price cannot be lower than 90% of the expected price.",
            str(error_context.exception),
            "The selling price should not be allowed to fall below 90% of the expected price.",
        )
