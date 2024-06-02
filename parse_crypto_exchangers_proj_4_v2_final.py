import multiprocessing as mp
from selenium.webdriver.common.by import By
import gspread
import time
import telebot
import threading
import random
#from selenium import webdriver
from collections import defaultdict
from seleniumwire import webdriver

#bot = telebot.TeleBot('6863128147:AAGgI6b2nlG2oI_mZuhDnUfJVtvsvhrDIFU') #--scum 
#bot = telebot.TeleBot('6792642771:AAGnRxqnMG4Nlm-CqBPjjVsAY3ICIWTMUQo') #--on/off 
bot = telebot.TeleBot('6871067941:AAEekaqtZ3MjwDMrrTO0xUdrJg37BLcqReo')

def get_data_from_google_table(): #вытягивание всей инфы из таблицы
    gc = gspread.service_account(filename='D:/1_MY PROGS/PARSERS/проект кирилла/mytest-411319-99861ed21234.json')
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1N-eSem5yEzAFLmCveUZNtnaYVJ_lPOKOvp3yVo4LK4M/edit#gid=0')
    worksheet = sh.sheet1
    list_of_exchangers_and_urls=[]
    for i in range(1,43,2):
        values_list = worksheet.col_values(i)
        list_of_exchangers_and_urls.append(values_list)
     
    # получение коллекции обменников; по итогу оказалось не нужно    
    exchangers=worksheet.row_values(2)
    result=[]
    for i in exchangers:
        y=i.split(", ")
        result.extend(y)
    result=set(result)
    result.discard("")
    # получение коллекции обменников; по итогу оказалось не нужно  
    return list_of_exchangers_and_urls, result #2 значение по итогу оказалось не нужно

def get_direction(url): #получение направление обмена из ссылки например - BTC-RUB
    direction=""
    for j in url[26:]:
        if j!=".":
            direction+=j
        else:
            break
    return direction

def parse_page(url): # вытягивание всех обменников представленных по ссылке
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    options1 = [{'proxy': {'http': 'http://vM2bF7:9fUlTFZMqQ@46.8.56.57:1050'}}, {'proxy': {'http': 'http://vM2bF7:9fUlTFZMqQ@45.151.145.246:1050'}}]

    driver = webdriver.Chrome(seleniumwire_options=random.choice(options1) , options=options)
    try:
        driver.get(url)                                          
        list_of_exchangers = driver.find_element(By.ID,"rates_block")
        list_of_exchangers = list_of_exchangers.find_element(By.ID,"content_table")
        list_of_exchangers = list_of_exchangers.find_element(By.TAG_NAME,"tbody")
        list_of_exchangers = list_of_exchangers.find_elements(By.TAG_NAME,"tr")
        #список объектов обменников на сайте получен
        names_of_exchangers_on_page = []
        for exchanger in list_of_exchangers:
            data = exchanger.find_element(By.CLASS_NAME,"bj")
            names_of_exchangers_on_page.append(data.text) #список названий обменников на сайте получен и добавлен
        
        return names_of_exchangers_on_page
        
    except Exception as ex:
        print(type(ex))
        f = open('erorr_log.txt', 'a')
        f.writelines(str(ex)+"\n\n\n")
        return [] 

def get_course(url, exch):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    options1 = [{'proxy': {'http': 'http://vM2bF7:9fUlTFZMqQ@46.8.56.57:1050'}}, {'proxy': {'http': 'http://vM2bF7:9fUlTFZMqQ@45.151.145.246:1050'}}]

    driver = webdriver.Chrome(seleniumwire_options=random.choice(options1) , options=options)
    try:
        driver.get(url)                                          
        list_of_exchangers = driver.find_element(By.ID,"rates_block")
        list_of_exchangers = list_of_exchangers.find_element(By.ID,"content_table")
        list_of_exchangers = list_of_exchangers.find_element(By.TAG_NAME,"tbody")
        list_of_exchangers = list_of_exchangers.find_elements(By.TAG_NAME,"tr")
        #список объектов обменников на сайте получен
        
        for exchanger in list_of_exchangers:
            data = exchanger.find_element(By.CLASS_NAME,"bj")
            if data.text==exch:
                courses=exchanger.find_elements(By.CLASS_NAME,"bi")
                for i in courses:
                    course=i.text
                    if course[:2]!="1 ":
                        course=''.join([x for x in course if x.isdigit() or x=="."])
                        return course
        return -1
        
    except Exception as ex:
        
        return -1

def get_message_to_bot(element):
    messege=""
    for key1, value1 in element.items():
        mylist=value1.values()

        D = defaultdict(list)
        for i,item in enumerate(mylist):
            D[item].append(i)
        D = {k:v for k,v in D.items() if len(v)>1}

        for i in D.keys():
            if i!=-1:
                for key, value in element.items():
                    for key2, value2 in value.items():
                        if value2==i:
                            messege+=str(key2)+" "+ str(value2) +"\n"
        messege="ПО ССЫЛКЕ- "+str(key1)+" СЛЕДУЮЩИЕ ПОВТОРЫ:\n"+messege
    return messege
             
def get_formated_data(element, result_structure_shared, lock):
    exchangers = element[1].split(", ")
    for url in element[2:]:
        names_of_exchangers_on_page = parse_page(url)
        if names_of_exchangers_on_page==[]: print("НИЧЕГО НЕ НАШЕЛ", url,end="\n\n")
        f = open('url_log.txt', 'a')
        f.writelines(url+" "+str(names_of_exchangers_on_page)+"\n\n\n")
        for exch in exchangers:
            if exch in names_of_exchangers_on_page:
                city = element[0]
                try:
                    for i in result_structure_shared:
                        if url in i:
                            x=get_course(url,exch)
                            i[url][exch]=x
                            break
                except Exception as ex:
                    print(ex)
            
        f.close()

def create_result_structure(data):
    result_structure=list()
    for i in data:
        city=i[0]
        exchangers=i[1].split(", ")
        for j in exchangers:
            
            flag=-1
            for element in result_structure:
                if j in element:
                    flag=result_structure.index(element)
            
            if flag==-1:
                result_structure.append({j:{city:[]}})
            else:
                flag1=False
                for k in result_structure[flag][j]:
                    print(k)
                    if k==city:
                        flag1=True
                if flag1==False:
                    result_structure[flag][j][city]=[]
    return result_structure

def create_result_structure1(data):
    result_structure=list()
    for i in data:
        city=i[0]
        exchangers=i[1].split(", ")
        #print(i[2:])
        for j in i[2:]:
            
            flag=-1
            for element in result_structure:
                if j in element:
                    flag=result_structure.index(element)
            
            if flag==-1:
                gap={}
                for exch in exchangers:
                    gap[exch]=-1
                result_structure.append({j:gap})
            # else:
            #     flag1=False
            #     for k in result_structure[flag][j]:
            #         if k==city:
            #             flag1=True
            #     if flag1==False:
            #         result_structure[flag][j][city]=[]
    return result_structure

def convert_structure_to_shared(structure):
    manager = mp.Manager()
    result_structure_shared = manager.list()

    for item in structure:
        converted_item = manager.dict()

        for key, value in item.items():
            converted_value = manager.dict()

            for inner_key, inner_value in value.items():
                converted_inner_value = inner_value
                converted_value[inner_key] = converted_inner_value

            converted_item[key] = converted_value

        result_structure_shared.append(converted_item)

    return result_structure_shared                

def convert_structure_to_common(shared):
    common = []

    for item in shared:
        converted_item = {}

        for key, value in item.items():
            converted_value = {}

            for inner_key, inner_value in value.items():
                converted_inner_value = inner_value
                converted_value[inner_key] = converted_inner_value

            converted_item[key] = converted_value

        common.append(converted_item)

    return common

def start_process():
    print('Starting', mp.current_process().name)

def main():
    main_data,y=get_data_from_google_table() 
    result_structure=create_result_structure1(main_data) 
    for i in result_structure:
        print(i)
    result_structure_shared=convert_structure_to_shared(result_structure)
    
    manager = mp.Manager()
    lock = manager.Lock()
    pool_size = mp.cpu_count() * 2
    pool_size=pool_size//2
    pool = mp.Pool(
        processes=pool_size,
        initializer=start_process
    )
    for element in main_data:
            x=pool.apply_async(get_formated_data,(element, result_structure_shared, lock,))
            x.wait(1)
    pool.close()
    pool.join()
    
    result_structure=convert_structure_to_common(result_structure_shared)
    for i in result_structure:
        print(i)
    print(len(result_structure))
    return result_structure

def repeat_check(dop_check):
    element_copy=[]
    for i in dop_check:
        i=i.split("\n")
        i.pop()

        x=[]
        for j in i:
            j=j.split(" ")
            if len(j)==5:
                j=j[2]
            else:
                j=tuple(j)
            x.append(j)
        element_copy.append(x)
    
    repeated_result=[]
    
    for i in element_copy:
        x={}
        for j in i[1:]:
            x[j[0]]=get_course(i[0],j[0])
        y={}
        y[i[0]]=x
        repeated_result.append(y)
    return repeated_result

@bot.message_handler(content_types='text')
def starter(message):
    if message.text=="/start":
        bot.send_message(message.chat.id, "Выбери команду")
    elif message.text=="/check":
        thread = threading.Thread(target=main_program, args=(message,))
        thread.start()
        thread.join()
    elif message.text=="/report":
        try:
            for i in result:
                x=get_message_to_bot(element=i)
                if x[-3]!="Ы":
                    dop_check.append(x)
            bot.send_message(message.chat.id, "жду 30 сек")
            time.sleep(30)
            bot.send_message(message.chat.id, "30 прошло, повторная проверка")
            for i in repeat_check(dop_check):
                print(i)
                x=get_message_to_bot(element=i)
                if x[-3]!="Ы":
                    bot.send_message(message.chat.id, x)
                           
        except Exception as ex:
            print(ex)            

def main_program(message):
    bot.send_message(message.chat.id, "Проверка началась")
    t1 = time.time()
    global result,dop_check
    result = main()
    dop_check=[] 
    
    t2 = time.time()
    print("Прошло за ", t2 - t1)
    bot.send_message(message.chat.id, "Проверка завершена")
    message.text="/report"
    starter(message)
    time.sleep(60*10)
    return main_program(message)

if __name__ == '__main__':
    bot.polling(non_stop = True, interval = 0)
    

