{% extends 'base.html' %}
{% load static %}

{% block title %}Ожидание{% endblock %}

{% block styles %}
<style>
    .waiting-container {
        width: 100%;
        height: 100vh;
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: 'Pixelify Sans', sans-serif;
    }

    #matrix {
        position: absolute;
        top: 0;
        left: 0;
        z-index: 1;
    }

    .overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.6);
        z-index: 2;
    }

    .content {
        position: relative;
        z-index: 3;
        text-align: center;
        color: #fff;
    }

    .title {
        font-size: 57.6px;
        color: #6bc108;
        text-shadow: 2.4px 2.4px 4.8px #000;
        font-weight: bold;
        margin-bottom: 24px;
        animation: pulse 2s infinite;
    }

    .loading {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .dot {
        width: 18px;
        height: 18px;
        background-color: #ffffff;
        border-radius: 50%;
        margin: 0 9.6px;
        animation: bounce 1.5s infinite ease-in-out;
    }

    .dot:nth-child(2) {
        animation-delay: 0.2s;
    }

    .dot:nth-child(3) {
        animation-delay: 0.4s;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.03); }
    }

    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-18px); }
    }
</style>
{% endblock %}

{% block content %}
<div class="waiting-container">
    <canvas id="matrix"></canvas>
    <div class="overlay"></div>
    <div class="content">
        <h1 class="title">Ожидаем ответов других игроков</h1>
        <div class="loading">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    </div>
</div>
<script src="{% static 'js/matrix.js' %}"></script>
{% endblock %}