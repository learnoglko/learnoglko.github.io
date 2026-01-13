def printFunc(text):
    temp = map(str, text);temp2, len_temp2 = list(temp), len(text)
    rangeTemp2 = range((len(temp2)+len_temp2)//2);result = []
    for i in rangeTemp2:result.append(temp2[i]);
    Print_result_STRING = f"string:"+f"".join(result);real_result_print_str = Print_result_STRING[7:]
    print(f"{real_result_print_str+"\n"}", end="");

printFunc("Hello, World!")