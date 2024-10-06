import vk_api
import networkx as nx
import pandas as pd
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import time

# Конфигурация графа
st.sidebar.subheader("Настройки графа")
width = st.sidebar.slider("Ширина", 500, 1200, 950)
height = st.sidebar.slider("Высота", 500, 1200, 700)
directed = st.sidebar.checkbox("Направленный граф", True)
physics = st.sidebar.checkbox("Физика", True)
hierarchical = st.sidebar.checkbox("Иерархический", False)
max_depth = st.sidebar.slider("Максимальная глубина", 1, 2, 1)  
max_friends = st.sidebar.slider("Максимальное количество друзей на пользователя", 50, 500, 100)  

# VK API Токен доступа
VK_ACCESS_TOKEN = 'vk1.a.E8Q9hRefOz6nSCgBeM1T0V-13VHkE4dE0QATAb-uzA7EUPjDm6uIrl97_4Ikm8WZeRwdtwl7biXsQDxkdhlTUcv9jOYAVU6zSnFAt0aRRK7AzHrsFtr8XPnJOaCfe7twNf4hbTiWb1HD4bsY0g5Hb_Rrek5PaQwfVfb8F5PS5IbYv5JbaI7zthot3e1R4RjntiTGnG113F0HQc3rjIdUiQ'

# Список VK ID участников группы
group_members = [
    {'VK ID': 290530655, 'ФИО': 'Алимов Исмаил Рифатович'},
    {'VK ID': None, 'ФИО': 'Баклашкин Алексей Андреевич'},
    {'VK ID': 1931147, 'ФИО': 'Брежнев Вячеслав Александрович'},
    {'VK ID': 207227130, 'ФИО': 'Волков Матвей Андреевич'},
    {'VK ID': None, 'ФИО': 'Гаев Роман Алексеевич'},
    {'VK ID': 24435047, 'ФИО': 'Кирьянов Павел Александрович'},
    {'VK ID': 138042735, 'ФИО': 'Кравцов Кирилл Егорович'},
    {'VK ID': 172244589, 'ФИО': 'Лавренченко Мария Кирилловна'},
    {'VK ID': 168420440, 'ФИО': 'Лагуткина Мария Сергеевна'},
    {'VK ID': 711398942, 'ФИО': 'Лыгун Кирилл Андреевич'},
    {'VK ID': None, 'ФИО': 'Орачев Алексей Валерьевич'},
    {'VK ID': None, 'ФИО': 'Панарин Родион Владимирович'},
    {'VK ID': 65657314, 'ФИО': 'Пешков Максим Юрьевич (староста)'},
    {'VK ID': 176183602, 'ФИО': 'Прозоров Евгений Иванович'},
    {'VK ID': 50933461, 'ФИО': 'Свинаренко Владислав Александрович'},
    {'VK ID': None, 'ФИО': 'Союзов Владимир Александрович'},
    {'VK ID': 198216820, 'ФИО': 'Хренникова Ангелина Сергеевна'},
    {'VK ID': None, 'ФИО': 'Черкасов Егор Юрьевич'},
    {'VK ID': 268235974, 'ФИО': 'Яминов Руслан Вильевич'}
]

# Получание VK ID, за исключением отсутствующих
vk_ids = [member['VK ID'] for member in group_members if member['VK ID'] is not None]

# Создание связи между VK ID и ФИО
group_vkid_to_name = {member['VK ID']: member['ФИО'] for member in group_members if member['VK ID'] is not None}

st.write("## Граф социальной сети VK")

def get_vk_session():
    session = vk_api.VkApi(token=VK_ACCESS_TOKEN)
    vk = session.get_api()
    return vk

def build_vk_graph(vk_ids, max_depth=1, max_friends=100):
    vk = get_vk_session()
    G = nx.Graph()

    processed_ids = set()
    queue = [(vk_id, 0) for vk_id in vk_ids]  

    private_profiles = set()  
    start_time = time.time()

    while queue:
        vk_id, depth = queue.pop(0)
        if vk_id in processed_ids:
            continue
        processed_ids.add(vk_id)

        G.add_node(vk_id)

        if depth >= max_depth:
            continue

        try:
            # Получение списка друзей
            response = vk.friends.get(user_id=vk_id, count=max_friends)
            friends = response.get('items', [])
            
            for friend_id in friends:
                if friend_id not in G:
                    G.add_node(friend_id)
                G.add_edge(vk_id, friend_id)

                if friend_id not in processed_ids:
                    queue.append((friend_id, depth + 1))  # друзья друзей

        except vk_api.exceptions.ApiError as e:
            error_code = e.code
            if error_code == 30:
                private_profiles.add(vk_id)
            else:
                st.write(f"Ошибка при получении друзей для VK ID {vk_id}: {e}")
            continue

        
    if private_profiles:
        st.info(f"Обнаружено {len(private_profiles)} приватных профилей. Их друзья недоступны.")

    return G

def convert_graph_to_streamlit_format(G, vk_ids, group_vkid_to_name):
    vk = get_vk_session()
    nodes = []
    edges = []

    # показатели центральности графа
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)

    # получение информации о пользователях на графике
    user_ids = [node for node in G.nodes if node not in group_vkid_to_name]
    user_info_dict = {}
    batch_size = 1000  

    for i in range(0, len(user_ids), batch_size):
        batch_ids = user_ids[i:i+batch_size]
        try:
            users_info = vk.users.get(user_ids=batch_ids)
            time.sleep(0.34)  
            for user_info in users_info:
                uid = user_info['id']
                
                user_info_dict[uid] = f"VK ID {uid}"
        except vk_api.exceptions.ApiError as e:
            
            for uid in batch_ids:
                user_info_dict[uid] = f"VK ID {uid}"  
            continue

    # создание узлов и ребер визуализации
    for node in G.nodes:
        if node in group_vkid_to_name:
            # полные имена участников
            full_name = group_vkid_to_name[node]
            profile_url = f"https://vk.com/id{node}"
            # информация по центральности
            centrality_info = (
                f"Центральность степенная: {degree_centrality[node]:.4f}\n"
                f"Центральность по посредничеству: {betweenness_centrality[node]:.4f}\n"
                f"Центральность по близости: {closeness_centrality[node]:.4f}\n"
                f"Центральность собственного вектора: {eigenvector_centrality[node]:.4f}\n"
                f"Профиль: {profile_url}"
            )
        else:
            # для остальных только VK ID
            full_name = user_info_dict.get(node, f"VK ID {node}")
            centrality_info = ""
            profile_url = f"https://vk.com/id{node}"

        nodes.append(Node(
            id=str(node),
            label=full_name,
            size=25,
            title=centrality_info
        ))

    for source, target in G.edges:
        edges.append(Edge(source=str(source), target=str(target)))

    # центральность участников группы
    centrality_data = []
    for vk_id in vk_ids:
        if vk_id in G.nodes:
            full_name = group_vkid_to_name.get(vk_id, f"VK ID {vk_id}")
            centrality_data.append({
                'VK ID': vk_id,
                'ФИО': full_name,
                'Центральность степенная': degree_centrality.get(vk_id, 0),
                'Центральность по посредничеству': betweenness_centrality.get(vk_id, 0),
                'Центральность по близости': closeness_centrality.get(vk_id, 0),
                'Центральность собственного вектора': eigenvector_centrality.get(vk_id, 0),
            })

    centrality_df = pd.DataFrame(centrality_data)
    
    centrality_df[['Центральность степенная', 'Центральность по посредничеству',
                   'Центральность по близости', 'Центральность собственного вектора']] = centrality_df[[
        'Центральность степенная', 'Центральность по посредничеству',
        'Центральность по близости', 'Центральность собственного вектора']].round(4)

    return nodes, edges, centrality_df

# Построение графа с друзьями друзей
graph = build_vk_graph(vk_ids, max_depth=max_depth, max_friends=max_friends)


components = list(nx.connected_components(graph))
node_to_component = {}
for idx, component in enumerate(components):
    for node in component:
        node_to_component[node] = idx

initial_components = set(node_to_component.get(vk_id) for vk_id in vk_ids if vk_id in node_to_component)


# Преобразования для streamlit
nodes, edges, centrality_df = convert_graph_to_streamlit_format(graph, vk_ids, group_vkid_to_name)

config = Config(
    width=width,
    height=height,
    directed=directed,
    physics=physics,
    hierarchical=hierarchical
)

# Создание графа с помощью streamlit-agraph
return_value = agraph(nodes=nodes, edges=edges, config=config)

# Отображение по графикам
st.write("### Центральность участников группы")
st.dataframe(centrality_df)
