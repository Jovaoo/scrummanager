document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();

            const formData = new FormData(form);
            const xhr = new XMLHttpRequest();

            xhr.open('POST', form.action, true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.setRequestHeader('X-CSRFToken', csrftoken);

            xhr.onload = function() {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    showNotification(response.message, response.status);
                    if (response.status === 'success') {
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 1000);
                    }
                } else {
                    showNotification('Ha ocurrido un error. Por favor, inténtelo de nuevo.', 'error');
                }
            };

            xhr.onerror = function() {
                showNotification('Ha ocurrido un error. Por favor, inténtelo de nuevo.', 'error');
            };

            xhr.send(formData);
        });
    }
});

function showNotification(message, type) {
    const container = document.getElementById('inner-messages-container');
    
    if (!container) {
        const messagesContainer = document.createElement('div');
        messagesContainer.id = 'messages-container';
        messagesContainer.className = 'fixed bottom-6 right-6 transform z-50 overflow-hidden';
        messagesContainer.innerHTML = '<div id="inner-messages-container" class="flex flex-col-reverse"></div>';
        document.body.appendChild(messagesContainer);
    }

    const notification = document.createElement('div');
    notification.className = `notification alert-${type} show`;
    notification.role = 'alert';
    notification.innerHTML = `
        <div class="notification__body">
            <p>${message}</p>
        </div>
        <div class="notification__progress button-${type}"></div>
    `;
    
    container.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('hide');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}
