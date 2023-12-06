const express = require('express');
const bcrypt = require('bcrypt');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const upload = multer({ dest: 'uploads/' });

const app = express();
app.use(express.json());
app.use(cors()); // Enable CORS for all routes
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

let users = [];
const adminCredentials = {
    username: 'mbard',
    password: 'admin123' // bcrypt хеш для 'admin123'
};
const adminHashedPassword ='$2b$10$EpXNavnh01lc9fUEllb/ZuTGLBAbzyV36QTOcPY59PONONI87WjSK';


app.post('/admin/login', async (req, res) => {
    const { username, password } = req.body;
    if (username === 'mbard') {
        const match = bcrypt.compare(password, adminHashedPassword);
        if (match) {
            res.json({ message: 'Admin login successful' });
        } else {
            res.status(401).send('Incorrect password');
        }
    } else {
        res.status(401).send('Incorrect username');
    }
});
app.post('/register', upload.single('photo'), async (req, res) => {
    try {
        const hashedPassword = await bcrypt.hash(req.body.password, 10);
        const user = {
            username: req.body.username,
            password: hashedPassword,
            name: req.body.name,
            group: req.body.group,
            variant: req.body.variant,
            phone: req.body.phone,
            photo: req.file.path
        };
        const userExists = users.some(u => u.username === user.username);
        if (userExists) {
            res.status(400).send('User already exists');
        } else {
            users.push(user);
            res.status(201).send('User created');
        }
    } catch {
        res.status(500).send();
    }
});

app.post('/login', async (req, res) => {
    const user = users.find(u => u.username === req.body.username);
    if (user == null) {
        return res.status(400).send('Cannot find user');
    }
    try {
        if (bcrypt.compare(req.body.password, user.password)) {

            const { password, ...userDataWithoutPassword } = user;
            res.json(userDataWithoutPassword);
        } else {
            res.send('Not Allowed');
        }
    } catch {
        res.status(500).send();
    }
});

app.put('/user/:username', (req, res) => {
    const { username } = req.params;
    const { name, group, variant, phone } = req.body;
    const userIndex = users.findIndex(u => u.username === username);

    if (userIndex !== -1) {
        // Оновлення інформації користувача
        users[userIndex] = { ...users[userIndex], name, group, variant, phone };
        res.json(users[userIndex]);
    } else {
        res.status(404).send('User not found');
    }
});

app.delete('/user/:username', (req, res) => {
    const { username } = req.params;
    users = users.filter(u => u.username !== username);
    res.send('User deleted');
});
app.put('/admin/edituser/:username', async (req, res) => {
    const { username } = req.params;
    const { newPassword } = req.body;

    const userIndex = users.findIndex(u => u.username === username);

    if (userIndex !== -1) {
        // Оновлення паролю користувача
        const hashedPassword = await bcrypt.hash(newPassword, 10);
        users[userIndex].password = hashedPassword;
        res.json(users[userIndex]);
    } else {
        res.status(404).send('User not found');
    }
});

app.listen(3000, () => console.log('Server running on port 3000'));
