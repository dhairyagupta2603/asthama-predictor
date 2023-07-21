'use client'

import Image from 'next/image'
import Link from 'next/link'
import React from 'react'

import SpireLogo from '@/public/spire_logo_sq.png'

import IIScLogo from '@/public/iisc_logo.png'

import { IUrl } from './_types'


interface IHeader {
  websiteName: string,
  aboutLink: IUrl,
  consentLink: IUrl,
}

const Header: React.FC<IHeader> = (props) => {
  return (
    <header className='bg-slate-400 border border-black'>
      <div className='flex justify-between'>

        <h2 className='text-2xl flex-grow pl-3 py-4 w-fit'>
          {props.websiteName} by Asquire Lab
        </h2>

        <Link href={props.aboutLink.url} className='text-xl px-3 h-fit my-auto'>About</Link>
        <Link href='#' className='text-xl pr-4 pl-3 h-fit my-auto'>Consent</Link>

        <div className='my-auto h-fit'>
          <div className='flex flex-row'>
          <Image 
            src={SpireLogo}
            width={65} height={35}
            alt='Spire Logo'
          />
          <Image 
            src={IIScLogo}
            width={65} height={35}
            alt='Spire Logo'
          />
          </div>
        </div>

      </div>
    </header>
  );
};

export default Header;
