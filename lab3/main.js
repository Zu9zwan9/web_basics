document.getElementById('myBtn').addEventListener('click', getData);

function getData() {
    fetch('https://randomuser.me/api/?results=5')
        .then((response) => response.json())
        .then((data) => {
            console.log(data);
            let people = data.results;
            let output = "";

            people.forEach(function (user) {
                const { picture, location, email } = user;

                output += `
                     <div class="card">
                         <img src="${picture.large}" alt="Фото користувача">
                         <ul class="list-group">
                             <li class="list-group-item">Поштовий індекс: ${location.postcode}</li>
                             <li class="list-group-item">Координати: ${location.coordinates.latitude}, ${location.coordinates.longitude}</li>
                             <li class="list-group-item">Email: ${email}</li>
                             <li class="list-group-item">Місто: ${location.city}</li>
                         </ul>
                     </div>
                `;
            });
            document.getElementById('output').innerHTML = output;
        });
};
