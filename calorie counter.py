import sys
import sqlite3
import csv

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox


class CalorieCounter(QMainWindow):  # главное окно
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/calorie counter.ui', self)  # загрузка интерфейса

        self.con = sqlite3.connect('./source/calorie counter db.db')  # подключение БД
        cur = self.con.cursor()

        row = cur.execute('SELECT * FROM user').fetchone()  # данные пользователя
        self.calorie_norm, self.protein_norm, self.fat_norm, self.carbohydrate_norm = row  # норма в день
        self.total_calorie, self.total_protein, self.total_fat, self.total_carbohydrate = 0, 0, 0, 0  # общие КБЖУ

        dates = cur.execute('SELECT date FROM dates').fetchall()  # все даты
        if len(dates):  # проверка на наличие дат
            with open('./source/list of food.csv', encoding='utf8') as file:
                food_list = list(csv.reader(file, delimiter=','))[1:]  # csv таблица с продуктами (без первого ряда)
                for i in dates:
                    day_calorie, day_protein, day_fat, day_carbohydrate = 0, 0, 0, 0  # КБЖУ в день
                    food_text = list()  # список строчек
                    food = cur.execute('SELECT name, amount FROM food WHERE date_id = '
                                       f'(SELECT id FROM dates WHERE date = "{i[0]}")').fetchall()  # продукты за дату
                    for j in range(len(food)):
                        # КБЖУ
                        characteristics = list(filter(lambda x: x[0] == food[j][0], food_list))[0]
                        calorie = round(float(characteristics[4]) / 100 * food[j][1])
                        protein = round(float(characteristics[1]) / 100 * food[j][1])
                        fat = round(float(characteristics[2]) / 100 * food[j][1])
                        carbohydrate = round(float(characteristics[3]) / 100 * food[j][1])

                        # добавление в обшее значение
                        self.total_calorie += calorie
                        self.total_protein += protein
                        self.total_fat += fat
                        self.total_carbohydrate += carbohydrate

                        # добавление в дневное значение
                        day_calorie += calorie
                        day_protein += protein
                        day_fat += protein
                        day_carbohydrate += carbohydrate

                        # добавление в список строчек
                        food_text.append(f'{food[j][0]} - {food[j][1]} г, Калории - {calorie}, Белки'
                                         f' - {protein}, Жиры - {fat}, Углеводы - {carbohydrate}')
                    self.text.appendPlainText(f'{i[0]}: Калории - {day_calorie}, Белки - {day_protein}, '
                                              f'Жиры - {day_fat}, Углеводы - {day_carbohydrate}')  # вывод даты
                    for j in food_text:  # вывод продуктов
                        self.text.appendPlainText(j)
            dates = len(dates)
            # включение кнопок
            self.add_day_btn.setEnabled(True)
            self.add_product_btn.setEnabled(True)
        else:
            dates = 1  # защита от деления на 0

        # изменение статистики
        self.statistics.setText(
            f'Калории (ккал): Рекомендуемые в день - {self.calorie_norm}, '
            f'Средние в день - {round(self.total_calorie / dates)}\n'
            f'Белки (г): Рекомендуемые в день - {self.protein_norm}, '
            f'Средние в день - {round(self.total_protein / dates)}\n'
            f'Жиры (г): Рекомендуемые в день - {self.fat_norm}, '
            f'Средние в день - {round(self.total_fat / dates)}\n'
            f'Углеводы (г): Рекомендуемые в день - {self.carbohydrate_norm}, '
            f'Средние в день - {round(self.total_carbohydrate / dates)}')

        # триггеры
        self.add_day_btn.clicked.connect(self.add_day)
        self.add_product_btn.clicked.connect(self.add_product)
        self.edit_characteristics_btn.clicked.connect(self.edit_characteristics)

    def add_day(self):  # добавление дня
        # вывод диалога
        dialog = DayAddDialog()
        dialog.exec()

        if dialog.clicked:
            cur = self.con.cursor()
            dates = cur.execute('SELECT date FROM dates').fetchall()

            if dialog.date not in map(lambda x: x[0], dates):  # проверка на повтор даты
                cur.execute(f'INSERT INTO dates(date) VALUES("{dialog.date}")')  # добавление
                self.con.commit()
                # вывод даты
                self.text.appendPlainText(f'{dialog.date}: Калории - 0, Белки - 0, Жиры - 0, Углеводы - 0')

            cur.close()

        self.add_product_btn.setEnabled(True)  # включение кнопки

    def add_product(self):  # добавление продукта
        dialog = ProductAddDialog()
        dialog.exec()

        if dialog.clicked:
            self.text.setPlainText('')  # очистка предыдущего вывода

            cur = self.con.cursor()
            cur.execute(
                f'INSERT INTO food(date_id, name, amount) VALUES((SELECT id FROM dates WHERE date = "{dialog.day}"), '
                f'"{dialog.product}", {dialog.amount})')  # добавление продукта в ДБ
            self.con.commit()

            self.total_calorie, self.total_protein, self.total_fat, self.total_carbohydrate = 0, 0, 0, 0
            dates = cur.execute('SELECT date FROM dates').fetchall()
            with open('./source/list of food.csv', encoding='utf8') as file:
                reader = list(csv.reader(file, delimiter=','))[1:]
                for i in dates:
                    day_calorie, day_protein, day_fat, day_carbohydrate = 0, 0, 0, 0
                    food_text = list()
                    food = cur.execute(
                        'SELECT name, amount FROM food WHERE date_id = '
                        f'(SELECT id FROM dates WHERE date = "{i[0]}")').fetchall()
                    for j in range(len(food)):
                        characteristics = list(filter(lambda x: x[0] == reader[j][0], reader))[0]
                        calorie = round(float(characteristics[4]) / 100 * food[j][1])
                        protein = round(float(characteristics[1]) / 100 * food[j][1])
                        fat = round(float(characteristics[2]) / 100 * food[j][1])
                        carbohydrate = round(float(characteristics[3]) / 100 * food[j][1])

                        self.total_calorie += calorie
                        self.total_protein += protein
                        self.total_fat += fat
                        self.total_carbohydrate += carbohydrate

                        day_calorie += calorie
                        day_protein += protein
                        day_fat += protein
                        day_carbohydrate += carbohydrate

                        food_text.append(f'{food[j][0]} - {food[j][1]} г, Калории - {calorie}, Белки'
                                         f' - {protein}, Жиры - {fat}, Углеводы - {carbohydrate}')
                    self.text.appendPlainText(f'{i[0]}: Калории - {day_calorie}, Белки - {day_protein}, '
                                              f'Жиры - {day_fat}, Углеводы - {day_carbohydrate}')
                    for j in food_text:
                        self.text.appendPlainText(j)

            dates = len(dates)
            self.statistics.setText(
                f'Калории (ккал): Рекомендуемые в день - {self.calorie_norm}, '
                f'Средние в день - {round(self.total_calorie / dates)}\n'
                f'Белки (г): Рекомендуемые в день - {self.protein_norm}, '
                f'Средние в день - {round(self.total_protein / dates)}\n'
                f'Жиры (г): Рекомендуемые в день - {self.fat_norm}, '
                f'Средние в день - {round(self.total_fat / dates)}\n'
                f'Углеводы (г): Рекомендуемые в день - {self.carbohydrate_norm}, '
                f'Средние в день - {round(self.total_carbohydrate / dates)}')

            cur.close()

    def edit_characteristics(self):  # изменение характеристики
        dialog = EditCharacteristicsDialog()
        dialog.exec()

        if dialog.clicked:
            # изменение нормы
            self.calorie_norm = round(dialog.calorie)
            self.protein_norm = round(dialog.protein)
            self.fat_norm = round(dialog.fat)
            self.carbohydrate_norm = round(dialog.carbohydrate)
            self.con.cursor().execute(
                f'UPDATE user SET calorie_norm = {self.carbohydrate_norm}, protein_norm = {self.protein_norm}, '
                f'fat_norm = {self.fat_norm}, carbohydrate_norm = {self.carbohydrate_norm}')  # добавление в ДБ

        dates = len(self.con.cursor().execute('SELECT date FROM dates').fetchall())
        if not dates:
            dates = 1
        self.statistics.setText(
            f'Калории (ккал): Рекомендуемые в день - {self.calorie_norm}, '
            f'Средние в день - {round(self.total_calorie / dates)}\n'
            f'Белки (г): Рекомендуемые в день - {self.protein_norm}, '
            f'Средние в день - {round(self.total_protein / dates)}\n'
            f'Жиры (г): Рекомендуемые в день - {self.fat_norm}, '
            f'Средние в день - {round(self.total_fat / dates)}\n'
            f'Углеводы (г): Рекомендуемые в день - {self.carbohydrate_norm}, '
            f'Средние в день - {round(self.total_carbohydrate / dates)}')

        self.add_day_btn.setEnabled(True)

    def closeEvent(self, event):
        dialog = ExitDialog()
        dialog.exec()

        if dialog.no_clicked:  # удаление из БД если нажали кнопку нет
            cur = self.con.cursor()
            cur.execute('DELETE FROM dates')
            cur.execute('DELETE FROM food')
            cur.execute('UPDATE user SET calorie_norm = 0, protein_norm = 0, fat_norm = 0, carbohydrate_norm = 0')
            self.con.commit()
            self.con.close()
        event.accept()  # закрытие


class DayAddDialog(QDialog):  # диалог добавления дня
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/day add dialog.ui', self)
        self.clicked = False
        self.add_btn.clicked.connect(self.click)

    def click(self):
        self.clicked = True  # кнопка "добавить" нажата
        self.date = self.calendar.selectedDate().toString('dd/MM/yyyy')  # дата
        self.close() # закрытие диалога


class ProductAddDialog(QDialog):  # диалог добавления продукта
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/product add dialog.ui', self)

        self.clicked = False
        self.con = sqlite3.connect('./source/calorie counter db.db')

        with open('./source/list of food.csv', encoding='utf8') as file:
            reader = map(lambda x: x[0], list(csv.reader(file, delimiter=','))[1:])
            self.product_combo_box.addItems(list(reader))

        dates = map(lambda x: x[0], self.con.cursor().execute('SELECT date FROM dates').fetchall())
        self.day_combo_box.addItems(dates)

        self.add_btn.clicked.connect(self.click)
        self.product_line_edit.textChanged.connect(self.search_food)
        self.day_line_edit.textChanged.connect(self.search_day)

    def click(self):
        self.clicked = True

        # информация о приёме пищи
        self.product = self.product_combo_box.currentText()
        self.amount = self.amount_spin_box.value()
        self.day = self.day_combo_box.currentText()

        self.close()

    def search_food(self):  # поиск продукта
        with open('./source/list of food.csv', encoding='utf8') as file:
            reader = map(lambda x: x[0], list(csv.reader(file, delimiter=','))[1:])
            tag = self.product_line_edit.text().lower()

            self.product_combo_box.clear()  # очистка комбобокса
            self.product_combo_box.addItems(list(filter(lambda x: tag in x.lower(), reader)))  # добавление в комбобокс

    def search_day(self):  # поиск дня
        self.day_combo_box.clear()
        dates = map(lambda x: x[0], self.con.cursor().execute(
            f'SELECT date FROM dates WHERE date LIKE "%{self.day_line_edit.text()}%"').fetchall())
        self.day_combo_box.addItems(dates)


class EditCharacteristicsDialog(QDialog):  # диалог изменения характеристики
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/edit physical characteristics dialog.ui', self)

        self.clicked = False
        self.edit_btn.clicked.connect(self.click)

    def click(self):
        self.clicked = True

        # формулы для вычисления норм
        coeff = {'Низкий': 1.25, 'Умеренный': 1.5, 'Интенсивный': 1.75}[self.physical_activity_level.currentText()]
        if self.sex.currentText() == 'Мужской':
            self.calorie = (10 * self.weight.value() + 6.25 * self.growth.value() + 5 * self.age.value() + 5) * coeff
        elif self.sex.currentText() == 'Женский':
            self.calorie = (10 * self.weight.value() + 6.25 * self.growth.value() + 5 * self.age.value() - 161) * coeff
        self.protein = self.weight.value() * 2
        self.fat = self.calorie * 0.25
        self.carbohydrate = self.calorie * 0.45

        self.close()


class ExitDialog(QDialog):  # диалог при выходе
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/exit dialog.ui', self)
        self.no_clicked = False

        self.yes_btn.clicked.connect(self.yes)
        self.no_btn.clicked.connect(self.no)

    def yes(self):
        self.close()

    def no(self):
        self.no_clicked = True  # нажато кнопка "нет"
        self.close()


app = QApplication(sys.argv)
ex = CalorieCounter()
ex.show()
sys.exit(app.exec())
