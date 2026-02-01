import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';

const AdminLayout = () => {
  return (
    <div className="flex min-h-screen bg-secondary-50">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-72">
        <Header />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
