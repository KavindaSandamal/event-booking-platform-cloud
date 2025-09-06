import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import App from '../App';
import authSlice from '../store/authSlice';

// Mock store
const mockStore = configureStore({
  reducer: {
    auth: authSlice,
  },
});

// Mock the API module
jest.mock('../utils/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

describe('App Component', () => {
  test('renders without crashing', () => {
    render(
      <Provider store={mockStore}>
        <App />
      </Provider>
    );
    
    // Check if the app renders without throwing
    expect(screen.getByText(/Event Booking Platform/i)).toBeInTheDocument();
  });

  test('shows login form when not authenticated', () => {
    render(
      <Provider store={mockStore}>
        <App />
      </Provider>
    );
    
    // Should show login form
    expect(screen.getByText(/Login/i)).toBeInTheDocument();
  });
});
