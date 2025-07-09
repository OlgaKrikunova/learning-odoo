from odoo import api, models


class PurchaseOrderLine(models.Model):  # определение новой модели, которая наследует purchase.order.line
    _inherit = "purchase.order.line"  # Указываем, что наследуем модель purchase.order.line

    @api.model_create_multi  # Декоратор @api.model_create_multi означает, что метод поддерживает создание сразу
    # нескольких записей (списком)
    def create(self, vals_list):  # Проходим по каждому словарю (каждой строке) в списке значений
        for line in vals_list:
            if not line.get("discount"):  # Если в словаре отсутствует поле 'discount' (или оно None/False),
                # то устанавливаем его значение по умолчанию — 5%
                line["discount"] = 5

        result = super().create(
            vals_list
        )  # Вызываем оригинальный метод create от родительского класса с обновлёнными значениями

        # for line in result:        # Вариант 1: проход по созданным строкам и обновление через метод write
        #     if not line.discount:
        #         line.write({'discount': 5})

        # for line in result:              # Вариант 2: прямое присвоение значения в поле discount
        #                                    (не рекомендуется, т.к. может не сработать правильно без save)
        #     if not line.discount:
        #       line.discount = 5  # set the discount to 5%

        return result
