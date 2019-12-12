import vk_api
import os, re
import json
from getpass4 import getpass
from tqdm import tqdm
import time, csv, random
from colorama import init, Fore, Back
init(convert=True)


def get_access_token(login='', password='', access_token=0): # функция получения access_token
    try:
        User = VK.users.get()
    except:
        print(Fore.RED+"Error") # вывод ошибки
    else:
        print(f"\nHello {User[0]['first_name']}")             # приветствие пользователю, авторизация прошла успешно
        with open('vk_config.v2.json', 'r') as data_file:     # открыть файл на чтение
            data = json.load(data_file)
        for x in data[login]['token'].keys():
            for y in data[login]['token'][x].keys():
                access_token = data[login]['token'][x][y]['access_token']
    return access_token                                        # вернуть access_token


def search_users(gr=[], list_users=[]): # функция получения ID пользователей в группах
    for i in tqdm(gr):
        try:
            id_gr=i['id']
            us=vk.method('groups.getMembers',{'group_id':id_gr, 'sort':1})['items'] # получить ID пользователя
            list_users.extend(us)       # внести ID в список
        except Exception as e:          # при возникновении ошибки уснуть на 2 сек.
            time.sleep(2)               # исключить слишком частое обращение к API ВК
    return list_users                   # вернуть список пользователя из найденных сообществ сети ВК

def get_base():                         # функция получения ID из базы по раннее отработанным комментариям
    try:
        with open('data_base.csv', 'r') as resultFile: # прочесть файл базы данных с ID
            reader = csv.reader(resultFile, delimiter=';')
            headers = next(reader)
            for row in reader:
                if re.search(r'\D', str(row[0])) or row[0]=='': continue # если повредилась база и в ней встретилось НЕ число продолжить
                past_id.add(int(row[0])) # внести ID в множество
    except IndexError:                   # в случае если база данных пуста
        pass                             # вернуть пустое множество
    return past_id                       # вернуть множество ID пользователей которым в прошлые сессии отправлялся комментарий


def get_user_name(info_user=0):                                  # функция получения имени пользователя
    user_name = vk.method('users.get',{'user_ids':info_user})[0] # вернуть имена пользователей
    for name in user_name:
        first_name=user_name['first_name']                       # получить имя пользователя
    return first_name


def create_comments(list_users=[], cap_params = None, count=0):  # функция создания комментария на стене пользователя ВК
    for info_user in list_users:
        count+=1
        result=[]
        try:
            first_name = get_user_name(info_user)
            info_wall = vk.method('wall.get', {'owner_id':info_user, 'count':1})['items'][0] # получить самую последнюю запись на стене
            time.sleep(1)                                                                    # исключить слишком частое обращение к API ВК
            if info_wall['comments']['can_post'] == 1:                                       # если стена открыта для комментирования
                if not cap_params:
                    vk.method('wall.createComment',{'owner_id':info_user, 'post_id': info_wall['id'], 'message':str(random.SystemRandom().choice(salut))+' '+first_name+'.'+' '+comment}) # отправить комментарий под записью
                    print(Fore.GREEN +'комментарий добавлен пользователю ' + '. ID: ' + str(info_user))
                    result.append(info_user)
                    result.append(first_name)
                    result.append(comment)
                    result.append(str(time.strftime("%Y-%m-%d")))
                    base.append(result)
                else:
                    vk.method('wall.createComment',{'owner_id':info_user, 'post_id': info_wall['id'], 'message':str(random.SystemRandom().choice(salut))+' '+first_name+'.'+' '+comment}, captcha_sid = cap_params[0], captcha_key = cap_params[1])
                    print(Fore.GREEN + 'комментарий добавлен пользователю ' + '. ID: ' + str(info_user))
                    result.append(info_user)
                    result.append(first_name)
                    result.append(comment)
                    result.append(str(time.strftime("%Y-%m-%d")))
                    base.append(result)
            else:
                time.sleep(0.5)                     # исключить слишком частое обращение к API ВК
                continue
        except vk_api.Captcha as vk_error:          # получение капчи
            cap_img, cap_sid = vk_error.url, vk_error.sid
            print(Fore.BLUE + '-ВНИМАНИЕ:')
            print(Fore.BLUE+'-Для продолжения необходимо перейти по ссылке и ввести код с картинки')
            print("Captcha solve required.\nURL:%s" % cap_img)
            cap_key = input("Captcha solve: ")      # ввести код с картинки
            list_users=list_users[count-1:]         # сократить список по ранее пройденным пользователям в данную сессию
            time.sleep(1)                           # исключить слишком частое обращение к API ВК
            create_comments(list_users, (cap_sid, cap_key), count) # повторно вызвать функцию создания комментария
        except vk_api.exceptions.ApiError as error: # временный запрет на использование API ВК
            if '[213]' in str(error):
                print(Fore.RED +' ВК заблокировал доступ к API. Попробуйте через 8 часов')
                break                               # в случае запрета использовать методы API прервать сессию и выйти из функции
            else:
                print(Fore.BLUE +'пользователь закрыл стену для комментариев или профиль является приватным  ' + '. ID: ' + str(info_user))
                continue                            # в случае возникнвения другой ошибки продолжить сессию
        except IndexError:
            continue
    return base


def quest_use_base(quest_use=''): # функция ответа использования базы
    if quest_use == "да": return True
    elif quest_use == "нет": return False
    # в случае ошибки вернуть None и повторить попытку


def create_base(headers=[['ID','first_name','Comment','datetime']]): # функция создания базы данных
    try:
        with open('data_base.csv', 'r') as resultFile: # в случае если сессии рассылки проводились ранее прочесть содержимое
            readcsv = csv.reader(resultFile)
    except FileNotFoundError:                          # в случае первой сессии и отсутствия файла
        with open('data_base.csv', 'w') as resultFile: # создать пустой файл с соответствующими заголовками
            wr = csv.writer(resultFile, delimiter=';')
            wr.writerows(headers)                      # записать столбцы


def print_info():                                      # функция вывода инструкции и порядка использования
    info_list=['Программа: comment_vk_wall', 'Служит для комментирования записей на стене пользователя сети ВК.','--------------------------------------------------',
               'ИНСТРУКЦИЯ:','--Введите ваш логин в формате +79170001020.', '--Введите пароль от своей страницы ВК.',
               '--Введите запрос для поиска групп ВК.', '--Введите несколько приветствий для пользователя через запятую',
               '--НАПРИМЕР: Салют, Доброго дня, Добрый день, Привет','--Введите комментарий который хотите отправить.',
               'Программа отправит ваш комментарий к записи на стене пользователей из групп с различными введеными вами приветствиями.',
               'При завершении в терминал будет выведен ID пользователей которым был отправлен комментарий.',
               'В случае если вы ранее использовали программу есть возможность избежать рассылки комментариев одним и тем же пользователям.',
               'Для этого используйте базу данных пользователей которым ранее был отправлен комментарий на стену',
               'В случае самого первого использования программа создаст пустую базу в формате с именем data_base.csv',
               'и при выполнении добавит в нее пользователей которым рассылается комментарий.', 'ПРЕДУПРЕЖДЕНИЕ:',
               'Существуют ограничения на использование методов API ВК.', 'В связи этим невозможно отправить более 40 комментариев за одну сессию.',
               'Программа не сохраняет ваши пароль и логин.','Авторизацию необходимо проходить каждый раз при запуске.',
               '--------------------------------------------------','Разработчик: Сурнов Алексей.', 'e-mail: alslight@list.ru']
    [print(Fore.RED+info_list[k]) if k==16 or k==17 or k==18 or k==19 or k==20 else print(Fore.YELLOW+info_list[k]) for k in range(len(info_list))]

if __name__ == "__main__":
                                                                        # запуск программы
    print_info()
    print(Fore.BLUE + '--------------------------------------------------')
    while True:
        print(Fore.GREEN + 'Введите логин: ', end='')                   # цветная печать
        login = input()                                                 # ввод логина
        password = getpass(prompt=Fore.GREEN + 'Введите ваш пароль: ')  # ввод пароля
        try:
            VK = vk_api.VkApi(login, password)
            VK.auth(reauth=True, token_only=False)                      # авторизация страницы
            VK = VK.get_api()
            access_token = get_access_token(login, password)            # вызвать функцию получения access_token
            break
        except vk_api.exceptions.BadPassword:                           # в случае неверного ввода пароля повторить попытку
            print(Fore.RED+'Неверное имя пользователя или пароль')
            print(Fore.YELLOW + 'Попрбоуйте снова')
        except vk_api.AuthError:                                        # в случае неверного ввода логина или пароля, а так же сбоя в соединении с интернетом повторить попытку
            print(Fore.RED + 'Неверное имя пользователя или пароль либо отсутствует подключение к интернету')
            print(Fore.YELLOW + 'Попрбоуйте снова')

    result, base, past_id = [],[], set()
    create_base()
    vk = vk_api.VkApi(token=access_token)
    print(Fore.BLUE + '--------------------------------------------------')
    while True:
        print(Fore.YELLOW+'введите запрос на группу: ', end='')
        name_group=input().strip()                       # запрос для поиска групп ВК
        print(Fore.YELLOW+'введите приветствие для пользователя через запятую: ', end='')
        salut=input().split(',')                         # список приветствий для пользователя
        print(Fore.YELLOW+'введите ваш комментарий: ', end='')
        comment=input().strip()                          # комментарий пользователю на стену
        if name_group=='' or comment=='' or salut==['']: # в случае если одна из переменных пуста повторить ввод
            print(Fore.RED + 'Ошибка: Вы не ввели запрос на группу, преветствие пользователя или комментарий')
            print(Fore.YELLOW + 'Попрбоуйте снова')
            continue
        else: break

    print(Fore.BLUE + '------------------------------------------------------------------------')
    print(Fore.YELLOW+ 'Идет поиск пользователей в группах')

    gr=vk.method('groups.search',{'q':name_group, 'sort':0})['items'] # получить группы
    list_users=set(search_users(gr))                                  # вызвать функцию получения ID участников сообщества ВК

    while True:
        print(Fore.BLUE+'------------------------------------------------------------------------')
        print(Fore.YELLOW+'Чтобы не повторять комментарии у одних и тех же пользователей рекомендуем использовать базу данных')
        print(Fore.YELLOW+'по пользователям которым они ранее отправлялись на стену')
        print(Fore.BLUE+'------------------------------------------------------------------------')
        print(Fore.YELLOW+'Использовать базу данных по ранее отработанным комментариям [да/нет]?: ', end='')
        quest_use=input().lower()
        past_id=get_base()

        if quest_use_base(quest_use)==True:
            list_users=list_users-past_id            # удаление пользователей из найденного множества если ранее им отправлялся комментарий с данной страницы
            break
        elif quest_use_base(quest_use)==False: break # не использовать базу данных
        else: print(Fore.RED+'Ошибка ввода: вы ввели '+quest_use+'. Пожалуйста попробуйте снова') # в случае если пользователь ошибся при вводе повторить запрос

    list_users=list(list_users)

    create_comments(list_users, cap_params = None, count=0) # вызвать функцию создания комментария на стене
    with open('data_base.csv', 'a') as resultFile:          # открыть в файл базы данных пользователей которым в данную сессию был отправлен комментарий на стену
        wr = csv.writer(resultFile, delimiter=';')
        for row in base:
            wr.writerow(row)                                # Добавить ID, имя, комментарий сессии, дату сессии в файл по соотвествующим столбцам

    print(Fore.BLUE + '------------------------------------------------------------------------')

    print(Fore.GREEN+ 'Комментарий добавлен следующим пользователям:')
    [[print(Fore.GREEN+str(int(j+1))+'. ID: '+str(base[j][0])) if i==0 else print(end='') for i in range(len(base[j]))] for j in range(len(base))]
    # вывести в терминал пользователей которым был добавлен комментарий
    os.remove('vk_config.v2.json')
    print(Fore.GREEN+'сессия завершилась')


