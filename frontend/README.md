# TISS Healthcare Frontend

A modern React frontend for the TISS Healthcare Management System, built with TypeScript and Material-UI.

## 🚀 Features

- **Dashboard**: Overview of healthcare operations with statistics
- **Patient Management**: CRUD operations for patient records
- **Claims Management**: Healthcare claim processing and tracking
- **Provider Management**: Healthcare provider administration
- **Health Plan Management**: Insurance plan configuration
- **XML Generator**: TISS 3.05.00 compliant XML generation and validation

## 🛠️ Tech Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for modern, responsive design
- **React Router** for navigation
- **Vite** for fast development and building
- **DataGrid** for advanced data tables

## 📦 Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

## 🚀 Development

1. **Start the development server:**
   ```bash
   npm run dev
   ```

2. **Open your browser:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🏗️ Building for Production

1. **Build the application:**
   ```bash
   npm run build
   ```

2. **Preview the production build:**
   ```bash
   npm run preview
   ```

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Layout.tsx      # Main layout with navigation
├── pages/              # Application pages
│   ├── Dashboard.tsx   # Main dashboard
│   ├── Patients.tsx    # Patient management
│   ├── Claims.tsx      # Claims management
│   ├── Providers.tsx   # Provider management
│   ├── HealthPlans.tsx # Health plan management
│   └── XMLGenerator.tsx # XML generation and validation
├── App.tsx             # Main application component
└── main.tsx            # Application entry point
```

## 🔧 Configuration

The frontend is configured to proxy API requests to the backend:

- **Development**: API calls to `/api/*` are proxied to `http://localhost:8000`
- **Production**: Update the API base URL in your environment configuration

## 🎨 UI Components

- **Responsive Design**: Mobile-first approach with Material-UI
- **Data Tables**: Advanced data grids with sorting, filtering, and pagination
- **Forms**: Comprehensive forms for data entry and editing
- **Navigation**: Sidebar navigation with mobile support
- **Theme**: Customizable Material-UI theme

## 📱 Responsive Design

The application is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile devices

## 🔗 API Integration

The frontend is designed to work with the TISS Healthcare API:

- **Authentication**: API key-based authentication
- **CRUD Operations**: Full CRUD for all entities
- **XML Generation**: Integration with TISS XML generation service
- **Validation**: XML validation against TISS schemas

## 🚀 Getting Started

1. **Ensure the backend is running** on port 8000
2. **Start the frontend development server**
3. **Navigate through the application** using the sidebar
4. **Test all features** including data management and XML generation

## 📚 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint (if configured)

## 🌟 Key Features

### Dashboard
- Overview statistics
- Recent activity feed
- Quick action buttons

### Patient Management
- Patient registration
- CPF validation
- Contact information
- Status tracking

### Claims Management
- Healthcare claim creation
- Status tracking (pending, approved, denied, paid)
- XML generation integration
- Value and date validation

### XML Generator
- TISS 3.05.00 compliance
- Real-time validation
- Download functionality
- Error reporting

## 🔒 Security Features

- API key authentication
- Input validation
- Secure data handling
- CORS configuration

## 🎯 Next Steps

- [ ] Connect to real backend API
- [ ] Implement real-time data updates
- [ ] Add advanced filtering and search
- [ ] Implement user authentication
- [ ] Add reporting and analytics
- [ ] Implement audit logging

## 📞 Support

For questions or issues, please refer to the main project documentation or contact the development team. 