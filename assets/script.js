    const apiUrl = "/api";
    const adminUrl = "/api/admin";

    // Helper: Get token from local storage
    const getToken = () => localStorage.getItem("token");

    // Helper: Fetch API with token
    const fetchWithAuth = async (url, options = {}) => {
        const token = getToken();
        if (!token) {
            alert("Not authenticated. Please log in first.");
            return { error: "Not authenticated" };
        }
    
        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        });
    
        if (response.status === 401) {
            alert("Session expired. Please log in again.");
            logout();
        }
        return response;
    };
    
    const addTrainForm = document.getElementById("addTrainForm");
    if (addTrainForm) {
        addTrainForm.addEventListener("submit", (event) => {
            event.preventDefault();
            if (trainName && source && destination && totalSeats) {
                addTrain(event);
            } else {
                alert("Please fill in all required fields.");
            }
        });
    }
    // User Login
    async function login(event) {
        event.preventDefault();
        const username = document.getElementById("username")?.value;
        const password = document.getElementById("password")?.value;

        if (!username || !password) {
            alert("Username and password are required!");
            return;
        }

        const response = await fetch(`${apiUrl}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        if (response.ok) {
            localStorage.setItem("token", data.token);
            if (data.role === "admin") {
                window.location.href = "/admin_dashboard";
            } else {
                window.location.href = "/dashboard";
            }
        } else {
            alert(data.error || "Login failed");
        }
    }

    // User Registration
    async function register(event) {
        event.preventDefault();
        const username = document.getElementById("username")?.value;
        const password = document.getElementById("password")?.value;
        const role = document.getElementById("role")?.value;

        if (!username || !password) {
            alert("Username and password are required!");
            return;
        }

        const response = await fetch(`${apiUrl}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password, role }),
        });

        const data = await response.json();
        if (response.ok) {
            alert("Registered successfully!");
            window.location.href = "/login";
        } else {
            alert(data.error || "Registration failed");
        }
    }

    // Add Train (Admin)
    async function addTrain(event) {
        event.preventDefault();
        const trainName = document.getElementById("trainName")?.value;
        const source = document.getElementById("source")?.value;
        const destination = document.getElementById("destination")?.value;
        const totalSeats = document.getElementById("totalSeats")?.value;

        if (!trainName || !source || !destination || !totalSeats) {
            alert("All fields are required to add a train!");
            return;
        }

        const response = await fetchWithAuth(`${adminUrl}/add_train`, {
            method: "POST",
            body: JSON.stringify({ train_name: trainName, source, destination, total_seats: totalSeats }),
        });

        const data = await response.json();
        if (response.ok) {
            alert("Train added successfully!");
            window.location.reload();
        } else {
            alert(data.error || "Failed to add train");
        }
    }

    // Check Seat Availability
    async function checkSeatAvailability(event) {
        event.preventDefault();
        const source = document.getElementById("checkSource")?.value;
        const destination = document.getElementById("checkDestination")?.value;

        if (!source || !destination) {
            alert("Source and destination are required!");
            return;
        }

        const response = await fetch(`${apiUrl}/seat_availability?source=${source}&destination=${destination}`);
        const data = await response.json();

        const results = document.getElementById("results");
        if (!results) {
            console.error("Results container not found");
            return;
        }

        results.innerHTML = "";

        if (response.ok) {
            if (data.trains?.length) {
                data.trains.forEach((train) => {
                    results.innerHTML += `<div class="card mt-2">
                        <div class="card-body">
                            <h5 class="card-title">${train.train_name}</h5>
                            <p>From: ${train.source} | To: ${train.destination}</p>
                            <p>Available Seats: ${train.available_seats}</p>
                        </div>
                    </div>`;
                });
            } else {
                results.innerHTML = `<div class="alert alert-warning">No trains found.</div>`;
            }
        } else {
            results.innerHTML = `<div class="alert alert-danger">${data.message || "Error fetching data"}</div>`;
        }
    }

    // Book Ticket
    async function bookTicket(event) {
        event.preventDefault();
        const trainId = document.getElementById("bookTrainId")?.value;

        if (!trainId) {
            alert("Train ID is required to book a ticket!");
            return;
        }

        const response = await fetchWithAuth(`${apiUrl}/book_seat`, {
            method: "POST",
            body: JSON.stringify({ train_id: trainId }),
        });

        const data = await response.json();
        if (response.ok) {
            alert("Ticket booked successfully!");
            window.location.reload();
        } else {
            alert(data.error || "Failed to book ticket");
        }
    }

    // Show Booking Details
    async function showBookings() {
        const response = await fetchWithAuth(`${apiUrl}/booking_details`);
        const data = await response.json();

        const results = document.getElementById("results");
        if (!results) {
            console.error("Results container not found");
            return;
        }

        results.innerHTML = "";

        if (response.ok) {
            if (data.bookings?.length) {
                data.bookings.forEach((booking) => {
                    results.innerHTML += `<div class="card mt-2">
                        <div class="card-body">
                            <h5 class="card-title">Booking ID: ${booking.booking_id}</h5>
                            <p>Train: ${booking.train_name}</p>
                            <p>From: ${booking.source} | To: ${booking.destination}</p>
                            <p>Time: ${booking.booking_time}</p>
                        </div>
                    </div>`;
                });
            } else {
                results.innerHTML = `<div class="alert alert-warning">No bookings found.</div>`;
            }
        } else {
            results.innerHTML = `<div class="alert alert-danger">${data.message || "Error fetching data"}</div>`;
        }
    }

    // Logout
    function logout() {
        localStorage.removeItem("token");
        document.getElementById('userInfo').innerText = '';
        window.location.href = "/";
    }

    async function fetchUserInfo() {
        const response = await fetchWithAuth('/api/current_user');
        const userData = await response.json();
        if (response.ok) {
            // Store user details in localStorage or display them
            document.getElementById('userInfo').innerText = `Welcome, ${userData.username}`;
        } else {
            console.error('Failed to fetch user information');
        }
    }
    fetchUserInfo();

    // Fetch and Display User Bookings
    async function fetchBookings() {
        const response = await fetchWithAuth(`${apiUrl}/booking_details`);
        const data = await response.json();

        const results = document.getElementById("results");
        if (!results) {
            console.error("Results container not found");
            return;
        }

        results.innerHTML = ""; // Clear previous results

        if (response.ok) {
            if (data.bookings?.length) {
                data.bookings.forEach((booking) => {
                    results.innerHTML += `
                        <div class="card mt-3">
                            <div class="card-body">
                                <h5 class="card-title">Booking ID: ${booking.booking_id}</h5>
                                <p><strong>Train:</strong> ${booking.train_name}</p>
                                <p><strong>Route:</strong> ${booking.source} → ${booking.destination}</p>
                                <p><strong>Time:</strong> ${booking.booking_time}</p>
                            </div>
                        </div>`;
                });
            } else {
                results.innerHTML = `<div class="alert alert-warning">You have no bookings yet.</div>`;
            }
        } else {
            results.innerHTML = `<div class="alert alert-danger">${data.message || "Failed to fetch bookings."}</div>`;
        }
    }

    // Add Event Listener for Back Button
    document.getElementById("backToDashboard")?.addEventListener("click", () => {
        window.location.href = "/dashboard";
    });

    // Logout Functionality
    function logout() {
        localStorage.removeItem("token"); // Clear token
        alert("Logged out successfully!");
        window.location.href = "/"; // Redirect to home page
    }

    // Add Logout Button Event Listener
    document.getElementById("logoutButton")?.addEventListener("click", logout);

    // Event bindings
    document.getElementById("loginForm")?.addEventListener("submit", login);
    document.getElementById("registerForm")?.addEventListener("submit", register);
    document.getElementById("addTrainForm")?.addEventListener("submit", addTrain);
    document.getElementById("checkAvailability")?.addEventListener("click", checkSeatAvailability);
    document.getElementById("viewBookings")?.addEventListener("click", showBookings);
    document.getElementById("bookTicketForm")?.addEventListener("submit", bookTicket);
    document.getElementById("logoutButton")?.addEventListener("click", logout);
