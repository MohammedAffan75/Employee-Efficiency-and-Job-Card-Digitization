import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';

const OperatorLayout = () => {
  return (
    <div className="flex min-h-screen bg-secondary-50 overflow-x-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-72 min-w-0">
        <Header />
        <main className="flex-1 p-6 min-w-0 overflow-x-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default OperatorLayout;
