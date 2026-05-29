import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';

import { AppShell } from '@/components/layout/AppShell';
import { ProtectedRoute } from '@/components/common/ProtectedRoute';
import { RoleGate } from '@/components/common/RoleGate';
import { useAuth } from '@/hooks/useAuth';

import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { StudentDashboardPage } from '@/pages/StudentDashboardPage';
import { StudentsListPage } from '@/pages/StudentsListPage';
import { StudentDetailPage } from '@/pages/StudentDetailPage';
import { UploadsPage } from '@/pages/UploadsPage';
import { PredictionsPage } from '@/pages/PredictionsPage';
import { CounselingPage } from '@/pages/CounselingPage';
import { AnalyticsPage } from '@/pages/AnalyticsPage';
import { ChatPage } from '@/pages/ChatPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { UsersPage } from '@/pages/UsersPage';
import { CoursesPage } from '@/pages/CoursesPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.18 }}
    >
      {children}
    </motion.div>
  );
}

function HomeRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'student') return <StudentDashboardPage />;
  return <DashboardPage />;
}

export function AppRouter() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          element={
            <ProtectedRoute>
              <AppShell>
                <PageTransition>
                  <Routes>
                    <Route path="/" element={<HomeRedirect />} />

                    <Route
                      path="/students"
                      element={
                        <RoleGate allow={['admin', 'faculty']}>
                          <StudentsListPage />
                        </RoleGate>
                      }
                    />
                    <Route
                      path="/students/:id"
                      element={
                        <RoleGate allow={['admin', 'faculty']}>
                          <StudentDetailPage />
                        </RoleGate>
                      }
                    />
                    <Route
                      path="/users"
                      element={
                        <RoleGate allow={['admin']}>
                          <UsersPage />
                        </RoleGate>
                      }
                    />
                    <Route
                      path="/courses"
                      element={
                        <RoleGate allow={['admin']}>
                          <CoursesPage />
                        </RoleGate>
                      }
                    />
                    <Route
                      path="/uploads"
                      element={
                        <RoleGate allow={['admin', 'faculty']}>
                          <UploadsPage />
                        </RoleGate>
                      }
                    />
                    <Route
                      path="/predictions"
                      element={
                        <RoleGate allow={['admin', 'faculty']}>
                          <PredictionsPage />
                        </RoleGate>
                      }
                    />
                    <Route
                      path="/counseling"
                      element={
                        <RoleGate allow={['admin', 'faculty']}>
                          <CounselingPage />
                        </RoleGate>
                      }
                    />
                    <Route
                      path="/analytics"
                      element={
                        <RoleGate allow={['admin', 'faculty']}>
                          <AnalyticsPage />
                        </RoleGate>
                      }
                    />
                    <Route
                      path="/chat"
                      element={
                        <RoleGate allow={['admin', 'faculty']}>
                          <ChatPage />
                        </RoleGate>
                      }
                    />
                    <Route path="/settings" element={<SettingsPage />} />

                    <Route path="*" element={<NotFoundPage />} />
                  </Routes>
                </PageTransition>
              </AppShell>
            </ProtectedRoute>
          }
          path="/*"
        />
      </Routes>
    </AnimatePresence>
  );
}
