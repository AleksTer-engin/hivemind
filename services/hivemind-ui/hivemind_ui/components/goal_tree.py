# components/goal_tree.py
import streamlit as st
import plotly.graph_objects as go

def render_goal_tree(goals_data):
    """Отрендерить дерево целей"""
    
    # Построить иерархию из данных
    labels = []
    parents = []
    values = []
    
    def add_node(node, parent=""):
        labels.append(node["name"])
        parents.append(parent)
        values.append(node.get("value", 0))
        
        for child in node.get("children", []):
            add_node(child, node["name"])
    
    add_node({"name": "Root", "children": goals_data})
    
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        textinfo="label+value+percent parent"
    ))
    
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    st.plotly_chart(fig, use_container_width=True)