import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { ApplicationsListPage } from '../pages/ApplicationsListPage';
import { ApplicationDetailPage } from '../pages/ApplicationDetailPage';
import { ServicesPage } from '../pages/ServicesPage';
import { SystemHealthPage } from '../pages/SystemHealthPage';
import { ProfilePage } from '../pages/ProfilePage';
import { AdminUsersPage } from '../pages/AdminUsersPage';
import { AuditLogPage } from '../pages/AuditLogPage';
import { CompletedApplicationsPage } from '../pages/CompletedApplicationsPage';
import { RejectedApplicationsPage } from '../pages/RejectedApplicationsPage';
import { ActionRequiredPage } from '../pages/ActionRequiredPage';
import { UnauthorizedPage } from '../pages/UnauthorizedPage';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        {/* Public Routes */}
        <Route index element={<Navigate to="/login" replace />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="services" element={<ServicesPage />} />
        <Route path="unauthorized" element={<UnauthorizedPage />} />

        {/* Authenticated Protected Routes (All authenticated roles) */}
        <Route
          path="dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="applications"
          element={
            <ProtectedRoute allowedRoles={['REVENUE_OFFICER', 'SENIOR_REVENUE_OFFICER', 'READ_ONLY_AUDITOR']}>
              <ApplicationsListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="applications/completed"
          element={
            <ProtectedRoute allowedRoles={['REVENUE_OFFICER', 'SENIOR_REVENUE_OFFICER', 'READ_ONLY_AUDITOR', 'DEPARTMENT_ADMINISTRATOR']}>
              <CompletedApplicationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="applications/rejected"
          element={
            <ProtectedRoute allowedRoles={['REVENUE_OFFICER', 'SENIOR_REVENUE_OFFICER', 'READ_ONLY_AUDITOR', 'DEPARTMENT_ADMINISTRATOR']}>
              <RejectedApplicationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="applications/action-required"
          element={
            <ProtectedRoute allowedRoles={['REVENUE_OFFICER', 'SENIOR_REVENUE_OFFICER', 'READ_ONLY_AUDITOR']}>
              <ActionRequiredPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="applications/:id"
          element={
            <ProtectedRoute allowedRoles={['REVENUE_OFFICER', 'SENIOR_REVENUE_OFFICER', 'READ_ONLY_AUDITOR']}>
              <ApplicationDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="completed"
          element={
            <ProtectedRoute allowedRoles={['REVENUE_OFFICER', 'SENIOR_REVENUE_OFFICER', 'READ_ONLY_AUDITOR', 'DEPARTMENT_ADMINISTRATOR']}>
              <CompletedApplicationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="rejected"
          element={
            <ProtectedRoute allowedRoles={['REVENUE_OFFICER', 'SENIOR_REVENUE_OFFICER', 'READ_ONLY_AUDITOR', 'DEPARTMENT_ADMINISTRATOR']}>
              <RejectedApplicationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="audit"
          element={
            <ProtectedRoute allowedRoles={['READ_ONLY_AUDITOR', 'DEPARTMENT_ADMINISTRATOR', 'SENIOR_REVENUE_OFFICER', 'REVENUE_OFFICER']}>
              <AuditLogPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="health"
          element={
            <ProtectedRoute allowedRoles={['DEPARTMENT_ADMINISTRATOR', 'READ_ONLY_AUDITOR', 'SENIOR_REVENUE_OFFICER', 'REVENUE_OFFICER']}>
              <SystemHealthPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />

        {/* Role-Restricted Admin Routes */}
        <Route
          path="admin/users"
          element={
            <ProtectedRoute allowedRoles={['DEPARTMENT_ADMINISTRATOR']}>
              <AdminUsersPage />
            </ProtectedRoute>
          }
        />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
};
