/** Uncomment the below codeblock if you want to add google analytics for more info please visit our docs analytics section */
/** 
import { useEffect } from 'react';
import Router from 'next/router';
import { initGA, logPageView } from 'analytics';
*/

import 'rc-drawer/assets/index.css';
import 'assets/css/react-slick.css';
import 'react-modal-video/css/modal-video.min.css';
import 'typeface-bree-serif';
import 'typeface-dm-sans';


export default function CustomApp({ Component, pageProps }) {
  return (
    <>
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;700&display=swap');
        body {
          font-family: 'Poppins', sans-serif;
        }
      `}</style>
      <Component {...pageProps} />
    </>
  );

  /** 
   useEffect(() => {
     initGA();
     logPageView();
     Router.events.on('routeChangeComplete', logPageView);
   }, []);
   */

  return <Component {...pageProps} />;
}


