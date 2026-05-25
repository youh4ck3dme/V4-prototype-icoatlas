import { Link } from 'react-router-dom';
import IcoAtlasLogo from '../components/IcoAtlasLogo';

const PaymentCancel = () => {
  return (
    <div className="min-h-[100dvh] bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white border border-slate-200 shadow-md rounded-xl p-8 text-center animate-fade-in">
        <IcoAtlasLogo className="mx-auto mb-6" />
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Platba zrušená</h1>
          <p className="text-slate-600">Vaša platba bola zrušená. Z účtu vám neboli stiahnuté žiadne prostriedky.</p>
        </div>
        <div className="space-y-3">
          <Link
            to="/dashboard"
            className="block w-full bg-[#0B4EA2] hover:bg-blue-800 text-white font-semibold py-3 px-4 rounded-lg transition-colors shadow-sm"
          >
            Späť na Dashboard
          </Link>
          <Link
            to="/profile"
            className="block w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-3 px-4 rounded-lg transition-colors border border-slate-200"
          >
            Skúsiť znova
          </Link>
        </div>
      </div>
    </div>
  );
};

export default PaymentCancel;

