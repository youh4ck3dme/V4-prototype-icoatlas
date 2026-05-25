import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import ProfilePage from "../pages/ProfilePage";
import { AuthContext } from "../contexts/AuthContext"; // It is named export, but check file first

// Mock react-router
vi.mock("react-router-dom", () => ({
  useNavigate: () => vi.fn(),
  Link: ({ children }) => <a>{children}</a>,
}));

describe("ProfilePage", () => {
  const mockUser = {
    full_name: "Test User",
    email: "test@example.com",
    tier: "free",
    created_at: "2023-01-01",
  };

  const renderWithAuth = (user = mockUser) => {
    return render(
      <AuthContext.Provider
        value={{ user, token: "fake-token", loading: false }}
      >
        <ProfilePage />
      </AuthContext.Provider>
    );
  };

  it("renders user details", () => {
    renderWithAuth();
    expect(screen.getByText("Test User")).toBeInTheDocument();
    expect(screen.getByText("test@example.com")).toBeInTheDocument();
    expect(screen.getByText("Zadarmo")).toBeInTheDocument();
  });

  it("shows upgrade options for free tier", () => {
    renderWithAuth({ ...mockUser, tier: "free" });
    expect(screen.getByText(/Upgrade na PRO/i)).toBeInTheDocument();
    expect(screen.getByText(/Upgrade na ENTERPRISE/i)).toBeInTheDocument();
  });

  it("hides enterprise upgrade for enterprise tier", () => {
    renderWithAuth({ ...mockUser, tier: "enterprise" });
    expect(
      screen.queryByText(/Upgrade na ENTERPRISE/i)
    ).not.toBeInTheDocument();
  });

  it("shows API Key section only for enterprise", () => {
    const { rerender, queryByText } = renderWithAuth({
      ...mockUser,
      tier: "pro",
    });
    expect(queryByText(/API Kľúče/i)).not.toBeInTheDocument();

    render(
      <AuthContext.Provider
        value={{
          user: { ...mockUser, tier: "enterprise" },
          token: "fake-token",
          loading: false,
        }}
      >
        <ProfilePage />
      </AuthContext.Provider>
    );
    expect(
      screen.getByRole("heading", { name: /API Kľúče/i })
    ).toBeInTheDocument();
  });
});
