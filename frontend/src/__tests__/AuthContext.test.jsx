import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import React, { useContext } from "react";
import { AuthProvider, useAuth } from "../contexts/AuthContext";

// Mock fetch
global.fetch = vi.fn();

// Test component to consume context
const TestComponent = () => {
  const { user, login, logout, register, loading } = useAuth();
  if (loading) return <div>Loading...</div>;
  return (
    <div>
      <div data-testid="user-email">{user?.email}</div>
      <button onClick={() => login("test@example.com", "password")}>
        Login
      </button>
      <button onClick={logout}>Logout</button>
      <button
        onClick={() => register({ email: "new@example.com", password: "pw" })}
      >
        Register
      </button>
    </div>
  );
};

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("provides initial state correctly", () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });

  it("handles login success", async () => {
    // Mock successful login response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: "fake-jwt-token" }),
    });

    // Mock fetchUser on token change
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ email: "test@example.com", tier: "free" }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await act(async () => {
      screen.getByText("Login").click();
    });

    await waitFor(() => {
      expect(localStorage.getItem("token")).toBe("fake-jwt-token");
    });
  });

  it("handles logout", async () => {
    localStorage.setItem("token", "existing-token");

    // Mock fetchUser for initial load
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ email: "test@example.com", tier: "free" }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() =>
      expect(screen.queryByText("Loading...")).not.toBeInTheDocument()
    );

    await act(async () => {
      screen.getByText("Logout").click();
    });

    expect(localStorage.getItem("token")).toBeNull();
  });
});
