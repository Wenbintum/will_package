def split_name(folname):
    '''
    split the name of folder     if name_list[0].startswith('W'): 
       met=name_list[0][:1]
       site=name_list[0][1:]
    else:
       met=name_list[0][:2]
       site=name_list[0][2:]
    r
    and return the metal, site, automatically   
    '''
    name_list=folname.split('O')
    if name_list[0].startswith('W'): 
       met=name_list[0][:1]
       site=name_list[0][1:]
    else:
       met=name_list[0][:2]
       site=name_list[0][2:]
    return met, site