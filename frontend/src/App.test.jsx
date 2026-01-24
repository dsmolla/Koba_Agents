import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'
import React from 'react'

// Mock supabase
vi.mock('./lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
      getUser: vi.fn().mockResolvedValue({ data: { user: null }, error: null }),
      onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
    }
  },
  getCurrentUser: vi.fn().mockResolvedValue(null),
  signOutUser: vi.fn(),
  signInUser: vi.fn(),
  signUpUser: vi.fn(),
  signInWithGoogleProvider: vi.fn(),
}))

describe('App', () => {
  it('renders sign up page by default', async () => {
    render(<App />)
    // Wait for loading to finish and Sign Up to appear
    await waitFor(() => {
      // "Sign Up" appears in title and button
      expect(screen.getAllByText(/Sign Up/i).length).toBeGreaterThan(0)
    })
  })
})
