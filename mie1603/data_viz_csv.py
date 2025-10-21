import matplotlib.pyplot as plt

filepath = 'final_test/csv/instance-jess-min_5000.csv'

def read_file(filepath):
  with open(filepath, 'r') as file:
    data = []
    for line in file:
      newline=line.split()
      data.append(newline)

  return data

def read_values(data):

  sol_dict={'t':[], 'bound':[],'obj':[], 'gap':[], 'node_count':[]}

  for i in range(len(data)):

    time = float(data[i][0].split(',')[0])
    sol_dict['t'].append(time)

    bound = float(data[i][1].split(',')[0])

    obj = float(data[i][2].split(',')[0])
    sol_dict['obj'].append(obj)

    # node_count = float(data[i][3].split(',')[0])
    # sol_dict['node_count'].append(node_count)

    if bound > 0.05:
        sol_dict['bound'].append(bound)
        gap = abs(bound - obj)/obj
        sol_dict['gap'].append(gap)
    else:
       sol_dict['bound'].append(None)

  return sol_dict

# filepath = '/Users/jingong/Github/MIE1603-Project/experiment_jess_3600/'
filepath = 'experiment_jess_1800/'
filepath = 'final_test/csv/'

instances = [
   'instance-jess-min_5000.csv',
   'instance-jess-min_10000.csv',
   'instance-jess-min_15000.csv',
   'instance-jess_5000.csv',
   'instance-jess_10000.csv',
   'instance-jess_15000.csv',
   'instance-jin_5000.csv',
   'instance-jin_10000.csv',
   'instance-jin_15000.csv',
   ]

# instances = [
#    'instance-jess_5000.csv',
#    'instance-jess_10000.csv',
#    'instance-jess_15000.csv']

lengths = ['5 km','10 km','15 km']#,'5 km removed','10 km removed','15 km removed', ]
colors= ['steelblue', 'orange', 'seagreen']#, 'steelblue', 'orange', 'seagreen']
# lengths = ['5 km','10 km','15 km'] # '8 km'

# data = read_file(filepath+instances[0])
# data_dict = read_values(data)

# x = data_dict['t']
# bound = data_dict['bound']
# obj = data_dict['obj']
# gap = data_dict['gap']
# node_count = data_dict['node_count']

# plt.plot(x, bound)
# plt.plot(x, obj)
# plt.show()

fig, axs = plt.subplots(3,3, sharex=True)

instances = [
   'instance-jess-min_5000.csv',
   'instance-jess-min_10000.csv',
   'instance-jess-min_15000.csv',
   ]



for i in range(len(instances)):

    data = read_file(filepath+instances[i])
    data_dict = read_values(data)

    x = data_dict['t']
    bound = data_dict['bound']
    obj = data_dict['obj']
    gap = data_dict['gap']
    print(gap[-1])
    node_count = data_dict['node_count']

    axs[0,i].plot(x, bound, label='Lower Bound')
    axs[0,i].plot(x, obj, label='Objective Value')
    axs[0,i].set_title(f'{instances[i]}')
    axs[0,i].set_ylabel('Profit')
    # axs[0,i].set_xlabel('Time (s)')
    axs[0,i].set_ylim([20000, 220000])
    axs[0,i].legend()


instances = [
   'instance-jess_5000.csv',
   'instance-jess_10000.csv',
   'instance-jess_15000.csv',
   ]



for i in range(len(instances)):

    data = read_file(filepath+instances[i])
    data_dict = read_values(data)

    x = data_dict['t']
    bound = data_dict['bound']
    obj = data_dict['obj']
    gap = data_dict['gap']
    node_count = data_dict['node_count']

    axs[1,i].plot(x, bound, label='Lower Bound')
    axs[1,i].plot(x, obj, label='Objective Value')
    axs[1,i].set_title(f'{instances[i]}')
    axs[1,i].set_ylabel('Profit')
    # axs[1,i].set_xlabel('Time (s)')
    axs[1,i].set_ylim([2500, 40000])
    axs[1,i].legend()


instances = [
   'instance-jin_5000.csv',
   'instance-jin_10000.csv',
   'instance-jin_15000.csv',
   ]



for i in range(len(instances)):

    data = read_file(filepath+instances[i])
    data_dict = read_values(data)

    x = data_dict['t']
    bound = data_dict['bound']
    obj = data_dict['obj']
    gap = data_dict['gap']
    node_count = data_dict['node_count']

    axs[2,i].plot(x, bound, label='Lower Bound')
    axs[2,i].plot(x, obj, label='Objective Value')
    axs[2,i].set_title(f'{instances[i]}')
    axs[2,i].set_ylabel('Profit')
    axs[2,i].set_xlabel('Time (s)')
    axs[2,i].set_ylim([-100, -40])
    axs[2,i].legend()

plt.show()



filepath = 'experiment_jess_1800/'
filepath = 'final_test/csv/'

lengths = ['5 km','10 km','15 km','5 km removed','10 km removed','15 km removed', ]
colors= ['steelblue', 'orange', 'seagreen', 'steelblue', 'orange', 'seagreen']
# lengths = ['5 km','10 km','15 km'] # '8 km'


instances = [
   'final_test/csv/instance-jess-min_5000.csv',
   'final_test/csv/instance-jess-min_10000.csv',
   'final_test/csv/instance-jess-min_15000.csv',
   'experiment_jess_1800\instance-jess-min-rem-aggressive_5000_rem_aggressive.csv',
   'experiment_jess_1800\instance-jess-min-rem-aggressive_10000_rem_aggressive.csv',
   'experiment_jess_1800\instance-jess-min-rem-aggressive_15000_rem_aggressive.csv'


   ]

for i in range(len(instances)):

    data = read_file(instances[i])#filepath+instances[i])
    data_dict = read_values(data)

    # x = data_dict['t']
    # bound = data_dict['bound']
    # obj = data_dict['obj']
    # gap = data_dict['gap']
    # node_count = data_dict['node_count']

    # plt.plot(x, gap)
    # # plt.plot(x, bound, label='Lower Bound')
    # # plt.plot(x, obj, label='Objective Value')
    # # plt.title(f'Profit for {instances[i]}')
    # plt.ylabel('Profit')
    # plt.xlabel('Time (s)')
    # plt.ylim([0,max(obj) + 10000])
    # plt.legend()
    # plt.show()

    time_first_bound = len(data_dict['t']) - len(data_dict['gap'])
    x = data_dict['t'][time_first_bound:]
    bound = data_dict['bound']
    obj = data_dict['obj'][time_first_bound:]
    gap = data_dict['gap']

    if 'rem' in lengths[i]:
        plt.plot(x, gap, label=lengths[i], color=colors[i])
    else:
       plt.plot(x, gap, label=lengths[i], linestyle='--', color=colors[i])
    plt.legend()
    # plt.title('MIP Gap for Min Instance')
    plt.xlabel('Time (s)')
    plt.ylabel('MIP Gap')
    plt.ylim([0,0.5])

plt.show()

