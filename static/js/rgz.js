// Базовый URL API
const API_URL = '/rgz/api';

// Универсальная функция вызова JSON-RPC
function callRPC(method, params, callback) {
    const requestId = Math.floor(Math.random() * 1000000);
    fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: method,
            params: params,
            id: requestId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            // Если есть ошибка, показываем сообщение и вызываем callback с ошибкой
            alert('Ошибка: ' + data.error.message);
            if (callback) callback(null, data.error);
        } else {
            // Успех — вызываем callback с результатом
            if (callback) callback(data.result, null);
        }
    })
    .catch(error => {
        alert('Сетевая ошибка: ' + error);
        if (callback) callback(null, { message: error });
    });
}

// Пример: регистрация
function registerUser(formData) {
    callRPC('user.register', {
        username: formData.username,
        password: formData.password,
        name: formData.name,
        service_type: formData.service_type,
        experience: parseInt(formData.experience),
        price: parseInt(formData.price),
        about: formData.about || ''
    }, function(result, error) {
        if (result) {
            alert('Регистрация успешна!');
            window.location.href = '/rgz/';  // перенаправление на главную
        }
    });
}

// Пример: вход
function loginUser(username, password) {
    callRPC('user.login', { username, password }, function(result, error) {
        if (result) {
            alert('Вход выполнен');
            window.location.href = '/rgz/';
        }
    });
}

// Пример: выход
function logoutUser() {
    callRPC('user.logout', {}, function(result, error) {
        if (result) {
            window.location.href = '/rgz/';
        }
    });
}

// Пример: поиск (вызывается из формы поиска)
function search(page = 1) {
    const name = document.getElementById('search-name').value;
    const service = document.getElementById('search-service').value;
    const expMin = document.getElementById('search-exp-min').value;
    const expMax = document.getElementById('search-exp-max').value;
    const priceMin = document.getElementById('search-price-min').value;
    const priceMax = document.getElementById('search-price-max').value;

    const params = {
        name: name,
        service_type: service,
        experience_min: expMin ? parseInt(expMin) : null,
        experience_max: expMax ? parseInt(expMax) : null,
        price_min: priceMin ? parseInt(priceMin) : null,
        price_max: priceMax ? parseInt(priceMax) : null,
        page: page
    };

    callRPC('search', params, function(result, error) {
        if (result) {
            displaySearchResults(result);
        }
    });
}

// Отображение результатов поиска
function displaySearchResults(data) {
    const container = document.getElementById('search-results');
    container.innerHTML = '';

    if (data.users.length === 0) {
        container.innerHTML = '<p>Ничего не найдено</p>';
        return;
    }

    data.users.forEach(user => {
        const card = document.createElement('div');
        card.className = 'user-card';
        card.innerHTML = `
            <h3>${user.name}</h3>
            <p><strong>Услуга:</strong> ${user.service_type}</p>
            <p><strong>Стаж:</strong> ${user.experience} лет</p>
            <p><strong>Цена:</strong> ${user.price} руб.</p>
            <p>${user.about}</p>
            <button onclick="viewProfile(${user.id})">Подробнее</button>
        `;
        container.appendChild(card);
    });

    // Пагинация
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    if (data.page > 1) {
        pagination.innerHTML += `<button onclick="search(${data.page - 1})">Предыдущая</button>`;
    }
    if (data.page < data.total_pages) {
        pagination.innerHTML += `<button onclick="search(${data.page + 1})">Следующая</button>`;
    }
    pagination.innerHTML += `<span> Страница ${data.page} из ${data.total_pages}</span>`;
}

// Просмотр профиля (публичного)
function viewProfile(userId) {
    callRPC('user.get_profile', { user_id: userId }, function(result, error) {
        if (result) {
            // Можно открыть модальное окно или перейти на отдельную страницу
            // В простом варианте покажем alert
            alert(`Имя: ${result.name}\nУслуга: ${result.service_type}\nСтаж: ${result.experience}\nЦена: ${result.price}\nО себе: ${result.about}`);
        }
    });
}

// Загрузка и отображение профиля текущего пользователя (на странице profile.html)
function loadMyProfile() {
    callRPC('user.get_profile', {}, function(result, error) {
        if (result) {
            document.getElementById('profile-username').innerText = result.username;
            document.getElementById('profile-name').innerText = result.name;
            document.getElementById('profile-service').innerText = result.service_type;
            document.getElementById('profile-experience').innerText = result.experience;
            document.getElementById('profile-price').innerText = result.price;
            document.getElementById('profile-about').innerText = result.about;
            document.getElementById('profile-hidden').checked = result.is_hidden;
            // Если админ, показываем доп. информацию
        }
    });
}

// Обновление профиля
function updateProfile() {
    const name = document.getElementById('edit-name').value;
    const service = document.getElementById('edit-service').value;
    const experience = parseInt(document.getElementById('edit-experience').value);
    const price = parseInt(document.getElementById('edit-price').value);
    const about = document.getElementById('edit-about').value;

    callRPC('user.update_profile', {
        name: name,
        service_type: service,
        experience: experience,
        price: price,
        about: about
    }, function(result, error) {
        if (result) {
            alert('Профиль обновлён');
            loadMyProfile(); // перезагрузить данные
        }
    });
}

// Скрыть/показать анкету
function toggleHide(checkbox) {
    callRPC('user.hide_profile', { hide: checkbox.checked }, function(result, error) {
        if (result) {
            alert('Статус скрытия изменён');
        }
    });
}

// Удалить аккаунт
function deleteAccount() {
    if (confirm('Вы уверены, что хотите удалить аккаунт?')) {
        callRPC('user.delete_account', {}, function(result, error) {
            if (result) {
                alert('Аккаунт удалён');
                window.location.href = '/rgz/';
            }
        });
    }
}

// Админские функции (пример)
function loadAllUsers(page = 1) {
    callRPC('admin.get_all_users', { page: page, per_page: 10 }, function(result, error) {
        if (result) {
            // отобразить список пользователей с кнопками редактирования/удаления
            console.log(result);
        }
    });
}

